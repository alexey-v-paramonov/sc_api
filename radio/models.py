from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

class AudioFormat:
    MP3 = 0
    AACPP = 1
    FLAC = 2

    choices = (
        (MP3, 'Mp3'),
        (AACPP, 'AAC++'),
        (FLAC, 'FLAC'),
    )

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


class BillingOptions:

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

class BaseRadio(models.Model):
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
    domain = models.CharField(
        "Domain name",
        null=True,
        blank=True,
        max_length=255  # 253 actually
    )

    status = models.PositiveSmallIntegerField(
        "Status",
        null=False,
        blank=True,
        choices=RadioHostingStatus.choices,
        default=RadioHostingStatus.PENDING,
    )

    is_blocked = models.BooleanField(
        default=False,
    )
    comment = models.TextField(null=True, blank=True)

    class Meta(object):
        abstract = True


class SelfHostedRadio(BaseRadio):
    ip = models.GenericIPAddressField(
        "IP Address",
        null=False,
        blank=False,
        max_length=255
    )
    ssh_username = models.CharField(
        "SSH user username",
        null=True,
        blank=True,
        max_length=255
    )

    ssh_password = models.CharField(
        "SSH user password",
        null=True,
        blank=True,
        max_length=255
    )

    ssh_port = models.PositiveIntegerField(
        "SSH port",
        default=22,
        null=False,
    )

class HostedRadio(BaseRadio):

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
        max_length=32,
        validators=[
            RegexValidator("^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$"),
        ],

    )
    initial_audio_format = models.CharField(
        "Audio format",
        max_length=10,
        choices=AudioFormat.choices,
        blank=True,
        null=True,
    )

    initial_bitrate = models.PositiveIntegerField("Bitrate", null=True, blank=True)
    initial_listeners = models.PositiveIntegerField("Maximum number of listeners", null=True, blank=True)
    initial_du = models.PositiveIntegerField("Disk quota", null=True, blank=True)

    is_demo = models.BooleanField(
        default=False,
    )
