from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from users.models import Language

User = get_user_model()


class Command(BaseCommand):
    help = 'Lists users who registered more than a week ago and have not created any services'

    def handle(self, *args, **options):
        # Calculate the date for "a week ago"
        today = timezone.now()
        week_ago = today - timedelta(days=7)

        # Get users who registered before a week ago
        users = User.objects.filter(
            date_joined__lt=week_ago,
            language=Language.ENG
        )

        # Import models here to avoid circular imports
        from mobile_application.models import AndroidApplication, IosApplication
        from catalog.models import Radio as CatalogRadio
        from payments.models import InvoiceRequest, Charge
        from radio.models import SelfHostedRadio, HostedRadio

        stalled_users = []

        for user in users:
            # Check if user has any mobile applications
            has_android_app = AndroidApplication.objects.filter(user=user).exists()
            has_ios_app = IosApplication.objects.filter(user=user).exists()
            has_mobile_app = has_android_app or has_ios_app
            
            # Check if user has any catalog radios
            has_catalog_radio = CatalogRadio.objects.filter(user=user).exists()
            
            # Check if user has any payments or charges
            has_payments = InvoiceRequest.objects.filter(user=user).exists()
            has_charges = Charge.objects.filter(user=user).exists()
            
            # Check if user has any hosted or self-hosted radios
            has_self_hosted = SelfHostedRadio.objects.filter(user=user).exists()
            has_hosted = HostedRadio.objects.filter(user=user).exists()

            # If user has none of the above services, add to stalled users
            if not (has_mobile_app or has_catalog_radio or has_payments or 
                    has_charges or has_self_hosted or has_hosted):
                stalled_users.append({
                    'id': user.id,
                    'email': user.email,
                    'date_joined': user.date_joined
                })

        # Output the results
        if stalled_users:
            self.stdout.write(self.style.SUCCESS(
                f'\nFound {len(stalled_users)} stalled user(s) who registered before {week_ago.date()}:\n'
            ))
            self.stdout.write('-' * 80)
            self.stdout.write(f'{"ID":<10} {"Email":<40} {"Registration Date":<30}')
            self.stdout.write('-' * 80)
            
            for user_data in stalled_users:
                self.stdout.write(
                    f'{user_data["id"]:<10} '
                    f'{user_data["email"]:<40} '
                    f'{user_data["date_joined"].strftime("%Y-%m-%d %H:%M:%S"):<30}'
                )
            
            self.stdout.write('-' * 80)
            self.stdout.write(self.style.SUCCESS(f'Total: {len(stalled_users)} user(s)\n'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\nNo stalled users found who registered before {week_ago.date()}\n'
            ))

