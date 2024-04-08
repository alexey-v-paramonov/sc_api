from django.db import models
from django.conf import settings
from users.models import Currency

class InvoiceRequest(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Owner",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

    email = models.EmailField("Email address")
    amount = models.PositiveIntegerField(
        null=False,
        blank=False,
    )
    is_paid = models.BooleanField(
        default=False,
    )

class ChargedServiceType:

    OTHER = 0
    RADIO_SELF_HOSTED = 1
    RADIO_HOSTED_STREAM = 2
    RADIO_HOSTED_DU = 3
    VOICEOVER = 3

    choices = (
        (OTHER, 'Other services'),
        (RADIO_SELF_HOSTED, 'Self hosted radio service'),
        (RADIO_HOSTED_STREAM, 'Hosted radio stream (traffic)'),
        (RADIO_HOSTED_DU, 'Hosted radio disk usage'),
        (VOICEOVER, 'Text to speech'),
    )

class Charge(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="User",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

    service_type = models.PositiveSmallIntegerField(
        "Service type",
        default=ChargedServiceType.OTHER,
        choices=ChargedServiceType.choices,
    )
    description = models.CharField(
        "Service description",
        null=True,
        blank=True,
        max_length=255
    )

    price = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    currency = models.PositiveSmallIntegerField(
        "Currency",
        default=Currency.USD,
        choices=Currency.choices,
    )

class UserPayment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="User",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    transaction_id = models.PositiveIntegerField(null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    currency = models.PositiveSmallIntegerField(
        "Currency",
        default=Currency.RUB,
        choices=Currency.choices,
    )
