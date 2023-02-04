from django.db import models
from django.conf import settings


class RadioHostingType:

    SELF_HOSTED = 0
    HOSTED = 1

    choices = (
        (SELF_HOSTED, 'Self-hosted'),
        (HOSTED, 'Hosted'),
    )


class RadioHostingStatus:

    PENDING = 0
    CHECKING = 1
    READY = 2

    choices = (
        (PENDING, 'Pending'),
        (CHECKING, 'Checking'),
        (READY, 'Ready'),
    )


class BillingOptions(object):

    SELF_HOSTED_RECURRING_PAYMENT = 1
    HOSTED_RECURRING_PAYMENT = 2

    choices = (
        (SELF_HOSTED_RECURRING_PAYMENT, 'Recurring payment'),
        (HOSTED_RECURRING_PAYMENT, 'Ready'),
    )


class RadioServer(models.Model):

    ip = models.GenericIPAddressField(
        "IP address",
        null=True,
        blank=True,
    )

    nodename = models.CharField(
        "Node subdomain name",
        null=False,
        blank=False,
        max_length=255
    )

    country = models.CharField(
        "Country",
        null=True,
        blank=True,
        max_length=255
    )

    provider = models.CharField(
        "Hosting provider",
        null=True,
        blank=True,
        max_length=255
    )

    available = models.BooleanField(
        default=True,
    )


class HostedRadio(models.Model):

    name = models.CharField(
        "Radio station name",
        null=True,
        blank=True,
        max_length=255
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Owner",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

    ts_created = models.DateTimeField(
        "Creation timestamp",
        auto_now_add=True
    )

    status = models.PositiveSmallIntegerField(
        "Status",
        null=False,
        blank=True,
        choices=RadioHostingStatus.choices,
        default=RadioHostingStatus.PENDING,
    )

    domain = models.CharField(
        "Domain name",
        null=True,
        blank=True,
        max_length=255  # 253 actually
    )

    server = models.ForeignKey(
        RadioServer,
        null=True,
        blank=True,
        on_delete=models.deletion.CASCADE
    )

    login = models.CharField(
        "Hosting login name",
        null=True,
        blank=True,
        unique=True,
        max_length=255
    )
