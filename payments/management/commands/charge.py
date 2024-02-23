import calendar
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template

from users.models import User
from payments.models import Charge, ChargedServiceType
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

class Command(BaseCommand):
    help = "Charge users daily"

    def handle(self, *args, **options):
        now = datetime.datetime.now()
        n_month_days = calendar.monthrange(now.year, now.month)[1]

        for user in User.objects.filter(balance__gt=0, is_staff=False):
            
            # Self hosted radios
            total_daily = 0

            for self_hosted_radio in user.selfhostedradio_set.all():
                price = self_hosted_radio.price()
                if price > 0:
                    daily_price = price / float(n_month_days)
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

            # Hosted radios
            for hosted_radio in user.hostedradio_set.exclude(is_demo=True):
                # Skip 5 days trial
                price = hosted_radio.price()
                if price > 0:
                    daily_price = price / float(n_month_days)
                    total_daily += daily_price
                    Charge.objects.create(
                        user=user,
                        service_type=ChargedServiceType.RADIO_HOSTED,
                        description=hosted_radio.login,
                        currency=user.currency,
                        price=daily_price
                    )
                    user.balance = user.balance - daily_price
                    user.save()
                
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

