import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User, EmailConfirmationToken

logger = logging.getLogger('django')

# Users registered before the email confirmation system existed (introduced in
# commit caf3ae4 on 2026-02-09) may have email_confirmed=False simply because
# the field didn't exist yet. Never consider those for deletion. We use the day
# after the feature launch (2026-02-10) to be safe.
# The value must be timezone-aware only when USE_TZ is enabled, otherwise MySQL
# (naive datetimes) rejects it.
EMAIL_CONFIRMATION_ERA_START = timezone.make_aware(datetime(2026, 2, 10)) if settings.USE_TZ else datetime(2026, 2, 10)


class Command(BaseCommand):
    help = (
        'Delete unconfirmed user accounts older than 7 days that have no related '
        'objects (no payments, charges, radios or apps). Only users registered '
        'after the email confirmation system was introduced are considered.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days after which to delete unconfirmed users (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        # Find unconfirmed users created after the email confirmation system
        # existed and before the cutoff date. Only delete "inactive" accounts:
        # users that never did anything and have no related objects (payments,
        # charges, radios or apps). Accounts that predate the email_confirmed
        # field are always ignored.
        unconfirmed_users = User.objects.filter(
            email_confirmed=False,
            date_joined__gte=EMAIL_CONFIRMATION_ERA_START,
            date_joined__lt=cutoff_date,
        ).exclude(
            userpayment__isnull=False,
        ).exclude(
            charge__isnull=False,
        ).exclude(
            selfhostedradio__isnull=False,
        ).exclude(
            hostedradio__isnull=False,
        ).exclude(
            androidapplication__isnull=False,
        ).exclude(
            iosapplication__isnull=False,
        )

        count = unconfirmed_users.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No inactive unconfirmed users to delete.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would delete {count} inactive unconfirmed users:'))
            for user in unconfirmed_users:
                self.stdout.write(f'  - {user.email} (created: {user.date_joined})')
        else:
            # Delete associated confirmation tokens first
            EmailConfirmationToken.objects.filter(user__in=unconfirmed_users).delete()

            # Log and delete users
            for user in unconfirmed_users:
                logger.info(f'Deleting inactive unconfirmed user: {user.email} (created: {user.date_joined})')
                self.stdout.write(f'  - Deleting {user.email}')

            deleted_count, _ = unconfirmed_users.delete()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} unconfirmed users older than {days} days.')
            )
            logger.info(f'Deleted {deleted_count} unconfirmed users older than {days} days')

        self.stdout.write(
            self.style.SUCCESS(f'Total delete candidates: {count}.')
        )
