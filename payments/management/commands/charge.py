import calendar
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template
from decimal import Decimal

from users.models import User
from payments.models import Charge, ChargedServiceType
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from radiotochka.billing import PRICE_PER_EXTRA_GB, PRICE_PER_EXTRA_GB_USD
from django.utils import timezone
from django.core.mail import EmailMessage

class Command(BaseCommand):
    help = "Charge users daily"

    def handle(self, *args, **options):
        now = timezone.now()
        print(f"Charge at {now}")
        n_month_days = calendar.monthrange(now.year, now.month)[1]
        paid_clients_rub = 0
        paid_clients_usd = 0
        total_rub = 0
        total_usd = 0

        for user in User.objects.filter(balance__gt=0, is_staff=False):
            
            # Self hosted radios
            total_daily = Decimal(0)

            for self_hosted_radio in user.selfhostedradio_set.all():
                price = self_hosted_radio.price()
                if price > 0:
                    daily_price = Decimal(Decimal(price) / Decimal(n_month_days))
                    total_daily += daily_price
                    description = self_hosted_radio.ip
                    if self_hosted_radio.domain:
                        description += f" ({self_hosted_radio.domain})"

                    if not Charge.objects.filter(
                        user=user,
                        service_type=ChargedServiceType.RADIO_SELF_HOSTED,
                        created__date=timezone.now().date(),
                        description=description
                    ).exists():
                        Charge.objects.create(
                            user=user,
                            service_type=ChargedServiceType.RADIO_SELF_HOSTED,
                            description=description,
                            currency=user.currency,
                            price=daily_price
                        )
                        user.balance = user.balance - daily_price
                        user.save()
                        print(f"User {user.email} self hosted radio charged {daily_price}, balance: {user.balance}")

            # Hosted radios
            for hosted_radio in user.hostedradio_set.exclude(is_demo=True):
                # Skip 5 days trial
                price = hosted_radio.price()
                if price > 0:
                    daily_price = Decimal(price) / Decimal(n_month_days)
                    total_daily += daily_price
                    if not Charge.objects.filter(
                        user=user,
                        service_type=ChargedServiceType.RADIO_HOSTED_STREAM,
                        created__date=timezone.now().date(),
                        description=hosted_radio.login,
                    ).exists():
                        Charge.objects.create(
                            user=user,
                            service_type=ChargedServiceType.RADIO_HOSTED_STREAM,
                            description=hosted_radio.login,
                            currency=user.currency,
                            price=daily_price
                        )
                        user.balance = user.balance - daily_price
                        user.save()
                        print(f"User {user.email} hosted radio {hosted_radio.login} charged {daily_price}, balance: {user.balance}")
                    # Disk usage extra
                    disk_quota = hosted_radio.get_disk_quota()
                    disk_quota_mb = disk_quota * 1024.
                    above_allowed_du = hosted_radio.disk_usage - disk_quota_mb
                    if above_allowed_du > 0:
                        du_price = PRICE_PER_EXTRA_GB_USD if user.is_usd() else PRICE_PER_EXTRA_GB
                        price_du_day = du_price / n_month_days * (above_allowed_du / 1024.)
                        total_daily += Decimal(price_du_day)
                        if not Charge.objects.filter(
                            user=user,
                            service_type=ChargedServiceType.RADIO_HOSTED_DU,
                            created__date=timezone.now().date(),
                        ).exists():
                            Charge.objects.create(
                                user=user,
                                service_type=ChargedServiceType.RADIO_HOSTED_DU,
                                description=str(above_allowed_du),
                                currency=user.currency,
                                price=price_du_day
                            )

                            user.balance = user.balance - Decimal(price_du_day)
                            user.save()
                            print(f"User {user.email} disk usage {above_allowed_du} charged {price_du_day}, balance: {user.balance}")

            if total_daily > 0:
                if user.is_rub():
                    total_rub += total_daily
                    paid_clients_rub += 1
                else:
                    total_usd += total_daily
                    paid_clients_usd += 1

            # Send payment notification
            if user.balance <= 0:
                template = "email/service_stop_en.html"
                subject = f"Streaming.center: account balance is negative, service have been suspended: {round(user.balance, 2)} {user.get_currency_display()}"
                if user.is_russian():
                    template = "email/service_stop_ru.html"
                    subject = f"Radio-Tochka.com: деньги закончились, услуги приостановлены {round(user.balance, 2)} {user.get_currency_display()}"

                template = get_template(template)
                content = template.render({"balance": round(user.balance, 2), "email": user.email, "currency": user.get_currency_display()})
                text_content = strip_tags(content)
                if user.is_russian():
                    msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [user.email,])
                else:
                    with get_connection(
                        host=settings.SC_EMAIL_HOST,
                        port=settings.SC_EMAIL_PORT,
                        username=settings.SC_EMAIL_HOST_USER,
                        password=settings.SC_EMAIL_HOST_PASSWORD,
                        use_ssl=settings.SC_EMAIL_USE_SSL,
                        use_tls=settings.SC_EMAIL_USE_TLS,
                    ) as connection:
                        msg = EmailMultiAlternatives(subject, text_content, settings.SC_ADMIN_EMAIL, [user.email,], connection=connection)

                msg.attach_alternative(content, "text/html")
                msg.send()

            elif user.balance < total_daily * 5:
                template = "email/payment_reminder_en.html"
                subject = f"Streaming.center: Low balance notification: {round(user.balance, 2)} {user.get_currency_display()}"
                if user.is_russian():
                    template = "email/payment_reminder_ru.html"
                    subject = f"Radio-Tochka.com: на балансе осталось {round(user.balance, 2)} {user.get_currency_display()}"

                template = get_template(template)
                content = template.render({"balance": round(user.balance, 2), "email": user.email, "currency": user.get_currency_display()})
                text_content = strip_tags(content)
                if user.is_russian():
                    msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [user.email,])
                else:
                    # Notify admin as well
                    sys_msg = EmailMessage(f"Low balance: {user.email}: {round(user.balance, 2)}", text_content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
                    sys_msg.attach_alternative(content, "text/html")
                    sys_msg.send()

                    with get_connection(
                        host=settings.SC_EMAIL_HOST,
                        port=settings.SC_EMAIL_PORT,
                        username=settings.SC_EMAIL_HOST_USER,
                        password=settings.SC_EMAIL_HOST_PASSWORD,
                        use_ssl=settings.SC_EMAIL_USE_SSL,
                        use_tls=settings.SC_EMAIL_USE_TLS,
                    ) as connection:
                        msg = EmailMultiAlternatives(subject, text_content, settings.SC_ADMIN_EMAIL, [user.email,], connection=connection)

                msg.attach_alternative(content, "text/html")
                msg.send()

        content = f"RUB paid clients: {paid_clients_rub}\nUSD paid clients: {paid_clients_usd}\n"
        msg = EmailMessage(f"Daily Income: {total_rub:.2f} RUB, {total_usd:.2f} USD", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
        msg.send()
