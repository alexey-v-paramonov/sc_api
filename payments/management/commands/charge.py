import calendar
import traceback
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
from django.db import transaction
from django.db.models import F, Q

class Command(BaseCommand):
    help = "Charge users daily"

    def open_connections(self):
        """Open both SMTP connections once, they are reused for the whole run:
        the default one (Radio-Tochka) and the Streaming.center one."""
        self.default_connection = get_connection()
        self.sc_connection = get_connection(
            host=settings.SC_EMAIL_HOST,
            port=settings.SC_EMAIL_PORT,
            username=settings.SC_EMAIL_HOST_USER,
            password=settings.SC_EMAIL_HOST_PASSWORD,
            use_ssl=settings.SC_EMAIL_USE_SSL,
            use_tls=settings.SC_EMAIL_USE_TLS,
        )
        for name, connection in self.smtp_connections():
            self.open_connection(name, connection)

    def smtp_connections(self):
        return (
            ("default", self.default_connection),
            ("streaming.center", self.sc_connection),
        )

    def connection_label(self, name, connection):
        """Describe the mail server behind a connection, so the logs tell which one failed."""
        host = getattr(connection, "host", None)
        if not host:
            # Console / file / locmem backends have no host
            return f"{name} ({connection.__class__.__module__})"
        username = getattr(connection, "username", None)
        return f"{name} ({host}:{getattr(connection, 'port', '?')} as {username})"

    def open_connection(self, name, connection):
        """Connect and log in. Never raises: a dead mail server must not stop the charges."""
        try:
            connection.open()
        except Exception as e:
            print(f"Failed to open the {self.connection_label(name, connection)} SMTP connection: {e}")

    def close_connection(self, name, connection):
        """Close the connection (quit + socket). Never raises."""
        try:
            connection.close()
        except Exception as e:
            print(f"Failed to close the {self.connection_label(name, connection)} SMTP connection: {e}")

    def close_connections(self):
        for name, connection in self.smtp_connections():
            self.close_connection(name, connection)

    def send_email(self, subject, content, from_email, recipients, use_sc_connection=False):
        """Send an html email over the shared connection. Never raises: any failure is printed
        and swallowed, so a broken mailbox / SMTP server does not stop the charge run."""
        if use_sc_connection:
            name, connection = "streaming.center", self.sc_connection
        else:
            name, connection = "default", self.default_connection

        try:
            text_content = strip_tags(content)
            # The connection is already open, so send_messages() reuses it instead of
            # opening and closing one per message
            msg = EmailMultiAlternatives(subject, text_content, from_email, list(recipients), connection=connection)
            msg.attach_alternative(content, "text/html")
            msg.send()
        except Exception as e:
            print(f"Failed to send email '{subject}' to {recipients} "
                  f"via {self.connection_label(name, connection)}: {e}")
            # The shared connection may be dead now (idle timeout, server restart), reconnect
            # so that the failure does not cascade to every following user
            self.close_connection(name, connection)
            self.open_connection(name, connection)

    def apply_charge(self, user, now, service_type, description, price, dedupe_by_description=True):
        """Create the charge record and deduct the balance in a single transaction, so a crash
        can never leave a charge without the matching deduction (which a re-run would then skip).

        Returns True if the user was charged, False if this service was already charged today.
        """
        price = Decimal(price)
        dedupe = {
            "user": user,
            "service_type": service_type,
            "created__date": now.date(),
        }
        if dedupe_by_description:
            dedupe["description"] = description

        with transaction.atomic():
            # Lock the user row so two overlapping runs cannot both pass the check below
            User.objects.select_for_update().get(pk=user.pk)

            if Charge.objects.filter(**dedupe).exists():
                return False

            Charge.objects.create(
                user=user,
                service_type=service_type,
                description=description,
                currency=user.currency,
                price=price,
            )
            # F() instead of user.save(): never overwrite a payment that landed during the run
            User.objects.filter(pk=user.pk).update(balance=F("balance") - price)

        user.refresh_from_db(fields=["balance"])
        return True

    def charge_self_hosted(self, user, now, n_month_days):
        """Charge all self hosted radios of the user, returns the daily total."""
        total_daily = Decimal(0)

        for self_hosted_radio in user.selfhostedradio_set.all():
            try:
                price = self_hosted_radio.price()
                if price <= 0:
                    continue

                daily_price = Decimal(Decimal(price) / Decimal(n_month_days))
                total_daily += daily_price
                description = self_hosted_radio.ip
                if self_hosted_radio.domain:
                    description += f" ({self_hosted_radio.domain})"

                if self.apply_charge(user, now, ChargedServiceType.RADIO_SELF_HOSTED, description, daily_price):
                    print(f"User {user.email} self hosted radio charged {daily_price}, balance: {user.balance}")
            except Exception as e:
                print(f"Failed to charge self hosted radio {self_hosted_radio.pk} of user {user.pk} ({user.email}): {e}")
                traceback.print_exc()

        return total_daily

    def charge_hosted(self, user, now, n_month_days):
        """Charge all hosted radios (stream + extra disk usage) of the user, returns the daily total."""
        total_daily = Decimal(0)

        for hosted_radio in user.hostedradio_set.exclude(is_demo=True):
            try:
                # Skip 5 days trial
                price = hosted_radio.price()
                if price <= 0:
                    continue

                daily_price = Decimal(price) / Decimal(n_month_days)
                total_daily += daily_price
                if self.apply_charge(user, now, ChargedServiceType.RADIO_HOSTED_STREAM, hosted_radio.login, daily_price):
                    print(f"User {user.email} hosted radio {hosted_radio.login} charged {daily_price}, balance: {user.balance}")

                # Disk usage extra
                disk_quota = hosted_radio.get_disk_quota()
                disk_quota_mb = disk_quota * 1024.
                above_allowed_du = hosted_radio.disk_usage - disk_quota_mb
                if above_allowed_du > 0:
                    du_price = PRICE_PER_EXTRA_GB_USD if user.is_usd() else PRICE_PER_EXTRA_GB
                    price_du_day = du_price / n_month_days * (above_allowed_du / 1024.)
                    total_daily += Decimal(price_du_day)
                    # Deduped per day only: the reported usage changes between runs, so matching
                    # on the description would charge twice on a re-run
                    if self.apply_charge(
                        user, now, ChargedServiceType.RADIO_HOSTED_DU, str(above_allowed_du), price_du_day,
                        dedupe_by_description=False,
                    ):
                        print(f"User {user.email} disk usage {above_allowed_du} charged {price_du_day}, balance: {user.balance}")
            except Exception as e:
                print(f"Failed to charge hosted radio {hosted_radio.pk} of user {user.pk} ({user.email}): {e}")
                traceback.print_exc()

        return total_daily

    def notify_user(self, user, total_daily):
        """Send the balance notification to the user. Never raises."""
        if user.balance <= 0:
            template = "email/service_stop_en.html"
            subject = f"Streaming.center: account balance is negative, service have been suspended: {round(user.balance, 2)} {user.get_currency_display()}"
            if user.is_russian():
                template = "email/service_stop_ru.html"
                subject = f"Radio-Tochka.com: деньги закончились, услуги приостановлены {round(user.balance, 2)} {user.get_currency_display()}"

            content = get_template(template).render({
                "balance": round(user.balance, 2),
                "email": user.email,
                "currency": user.get_currency_display(),
            })

            if user.is_russian():
                self.send_email(subject, content, settings.ADMIN_EMAIL, [user.email,])
            else:
                self.send_email(subject, content, settings.SC_ADMIN_EMAIL, [user.email,], use_sc_connection=True)

        elif user.balance < total_daily * 5:
            template = "email/payment_reminder_en.html"
            subject = f"Streaming.center: Low balance notification: {round(user.balance, 2)} {user.get_currency_display()}"
            if user.is_russian():
                template = "email/payment_reminder_ru.html"
                subject = f"Radio-Tochka.com: на балансе осталось {round(user.balance, 2)} {user.get_currency_display()}"

            content = get_template(template).render({
                "balance": round(user.balance, 2),
                "email": user.email,
                "currency": user.get_currency_display(),
            })

            if user.is_russian():
                self.send_email(subject, content, settings.ADMIN_EMAIL, [user.email,])
            else:
                # Notify admin as well
                self.send_email(
                    f"Low balance: {user.email}: {round(user.balance, 2)}",
                    content,
                    settings.ADMIN_EMAIL,
                    [settings.ADMIN_EMAIL,],
                )
                self.send_email(subject, content, settings.SC_ADMIN_EMAIL, [user.email,], use_sc_connection=True)

    def handle(self, *args, **options):
        now = timezone.now()
        print(f"Charge at {now}")
        n_month_days = calendar.monthrange(now.year, now.month)[1]
        paid_clients_rub = 0
        paid_clients_usd = 0
        total_rub = 0
        total_usd = 0
        failed_users = 0

        self.open_connections()
        try:
            for user in User.objects.filter(Q(balance__gt=0) | Q(id__in=[2775, 2774]), is_staff=False):

                total_daily = Decimal(0)
                try:
                    total_daily += self.charge_self_hosted(user, now, n_month_days)
                    total_daily += self.charge_hosted(user, now, n_month_days)
                except Exception as e:
                    # Anything unexpected for this user must not stop the whole run
                    failed_users += 1
                    print(f"Failed to charge user {user.pk} ({user.email}): {e}")
                    traceback.print_exc()
                    continue

                if total_daily > 0:
                    if user.is_rub():
                        total_rub += total_daily
                        paid_clients_rub += 1
                    else:
                        total_usd += total_daily
                        paid_clients_usd += 1

                # Send payment notification
                try:
                    self.notify_user(user, total_daily)
                except Exception as e:
                    # Rendering a template / building the message must not stop the run either
                    print(f"Failed to notify user {user.pk} ({user.email}): {e}")
                    traceback.print_exc()

            content = f"RUB paid clients: {paid_clients_rub}\nUSD paid clients: {paid_clients_usd}\n"
            if failed_users:
                content += f"Failed users: {failed_users}\n"
            subject = f"Daily Income: {total_rub:.2f} RUB, {total_usd:.2f} USD"
            msg = EmailMessage(subject, content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,], connection=self.default_connection)
            try:
                msg.send()
            except Exception as e:
                print(f"Failed to send email '{subject}' "
                      f"via {self.connection_label('default', self.default_connection)}: {e}")
        finally:
            # Quit both sessions on any exit: normal end, crash or Ctrl-C
            self.close_connections()
