import calendar
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template
from decimal import Decimal
from users.models import Currency

from users.models import User
from payments.models import Charge, ChargedServiceType
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from radiotochka.billing import PRICE_PER_EXTRA_GB, PRICE_PER_EXTRA_GB_USD
from django.utils import timezone

class Command(BaseCommand):
    help = "Charge users daily"

    def handle(self, *args, **options):
        now = timezone.now()
        n_month_days = calendar.monthrange(now.year, now.month)[1]

        for user in User.objects.filter(balance__gt=0, is_staff=False):
            
            # Self hosted radios
            total_daily = Decimal(0)

            for self_hosted_radio in user.selfhostedradio_set.all():
                price = self_hosted_radio.price()
                if price > 0:
                    daily_price = Decimal(price / Decimal(n_month_days))
                    total_daily += daily_price
                    Charge.objects.create(
                        user=user,
                        service_type=ChargedServiceType.RADIO_SELF_HOSTED,
                        description=self_hosted_radio.ip,
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
                    daily_price = price / Decimal(n_month_days)
                    total_daily += daily_price
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


            # Send payment notification
            if user.balance < total_daily * 7:
                template = "email/payment_reminder_en.html"
                subject = f"Streaming.center: Low balance notification: {round(user.balance, 2)} {user.get_currency_display()}"
                if user.is_russian():
                    template = "email/payment_reminder_ru.html"
                    subject = f"Radio-Tochka.com: на балансе осталось {round(user.balance, 2)} {user.get_currency_display()}"

                template = get_template(template)
                content = template.render({"balance": round(user.balance, 2), "email": user.email, "currency": user.get_currency_display()})
                text_content = strip_tags(content)
                #msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [user.email,])
                msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [settings.ADMIN_EMAIL,])
                msg.attach_alternative(content, "text/html")
                msg.send()

