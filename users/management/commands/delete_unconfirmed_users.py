from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import User, EmailConfirmationToken
import logging

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = 'Delete unconfirmed user accounts older than 7 days'

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
        
        # Find unconfirmed users created before cutoff date
        unconfirmed_users = User.objects.filter(
            email_confirmed=False,
            date_joined__lt=cutoff_date
        )
        
        count = unconfirmed_users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No unconfirmed users to delete.'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would delete {count} unconfirmed users:'))
            for user in unconfirmed_users:
                self.stdout.write(f'  - {user.email} (created: {user.date_joined})')
        else:
            # Delete associated confirmation tokens first
            EmailConfirmationToken.objects.filter(user__in=unconfirmed_users).delete()
            
            # Log and delete users
            for user in unconfirmed_users:
                logger.info(f'Deleting unconfirmed user: {user.email} (created: {user.date_joined})')
                self.stdout.write(f'  - Deleting {user.email}')
            
            deleted_count, _ = unconfirmed_users.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} unconfirmed users older than {days} days.')
            )
            logger.info(f'Deleted {deleted_count} unconfirmed users older than {days} days')
