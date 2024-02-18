from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

class AudioFormat:
    MP3 = "mp3"
    AACPP = "aac++"
    FLAC = "flac"

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

class ServiceType:

    STREAM = 1
    DISK = 2

    choices = (
        (STREAM, 'Stream traffic'),
        (DISK, 'Disk usage'),
    )


class RadioHostingStatus:

    PENDING = 0
    CHECKING = 1
    READY = 2
    BEING_CREATED = 3
    BEING_DELETED = 4
    SUSPENDED = 5
    ERROR = 6

    choices = (
        (PENDING, 'Pending'),
        (CHECKING, 'Checking'),
        (READY, 'Ready'),
        (BEING_CREATED, 'Being created'),
        (BEING_DELETED, 'Being deleted'),
        (SUSPENDED, 'Suspended'),
        (ERROR, 'Error'),
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
    debug_msg = models.TextField(null=True, blank=True)

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

class HostedRadioService(models.Model):
    radio = models.ForeignKey(
        HostedRadio,
        null=False,
        blank=False,
        on_delete=models.deletion.CASCADE
    )

    service_type = models.PositiveSmallIntegerField(
        "Service type",
        choices=AudioFormat.choices,
        blank=False,
        null=False,
    )

    channel_id = models.PositiveIntegerField(
        "Stream channel ID",
        blank=True,
        null=True,
    )
    bitrate = models.PositiveIntegerField("Bitrate", null=True, blank=True)
    listeners = models.PositiveIntegerField("Maximum number of listeners", null=True, blank=True)
    du = models.PositiveIntegerField("Disk quota", null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
