from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.db.models import Sum
from django.utils import timezone

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

class CopyrightType:

    LEGAL = 1
    NO_COPYRIGHT = 2
    TEST = 3

    choices = (
        (LEGAL, 'Has legal documents'),
        (NO_COPYRIGHT, 'No copyrighted content is used'),
        (TEST, 'Test account'),
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
        max_length=255, 
        unique=True
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
        unique=True,
        null=False,
        blank=False,
        max_length=255,
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
    custom_price = models.DecimalField(max_digits=12, decimal_places=6, blank=True, null=True)
    is_unbranded = models.BooleanField(
        default=False,
    )

    def is_trial_period(self):
        return (timezone.now() - self.ts_created).days < settings.FREE_TRIAL_DAYS

    def price(self):
        if self.custom_price is not None:
            return self.custom_price
        if self.is_blocked:
            return 0

        if self.status != RadioHostingStatus.READY:
            return 0

        if self.user.is_rub():
            return settings.BASE_PRICE_RUB
        return settings.BASE_PRICE_USD


class HostedRadio(BaseRadio):

    server = models.ForeignKey(
        RadioServer,
        null=False,
        blank=False,
        on_delete=models.deletion.CASCADE
    )

    login = models.CharField(
        "Hosting login name",
        null=True,
        blank=True,
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

    copyright_type = models.PositiveSmallIntegerField(
        "Copyright settings",
        choices=CopyrightType.choices,
        blank=True,
        null=True,
    )

    is_demo = models.BooleanField(
        default=False,
    )
    disk_usage = models.PositiveIntegerField("Disk usage", null=False, default=0, blank=True)
    def get_disk_quota(self):
        disk_quota = self.services.filter(service_type=ServiceType.DISK).last()
        if not disk_quota:
            return 0
        return disk_quota.du

    def price(self):
        if self.status != RadioHostingStatus.READY or self.is_demo:
            return 0
        if self.is_blocked:
            return 0        
        return self.services.aggregate(Sum('price'))['price__sum'] or 0.

    class Meta(object):
        unique_together = (
            ("login", "server"),
        )

class HostedRadioService(models.Model):
    radio = models.ForeignKey(
        HostedRadio,
        null=False,
        blank=False,
        on_delete=models.deletion.CASCADE,
        related_name='services'
    )

    service_type = models.PositiveSmallIntegerField(
        "Service type",
        choices=ServiceType.choices,
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
    class Meta(object):
        unique_together = (
            ("channel_id", "radio"),
        )


class PortRegistry(models.Model):

    radio = models.ForeignKey(
        HostedRadio,
        null=False,
        blank=False,
        on_delete=models.deletion.CASCADE
    )

    channel_id = models.PositiveIntegerField(null=True, blank=True)
    dj_id = models.PositiveIntegerField(null=True, blank=True)

    port = models.PositiveIntegerField(null=False, blank=False)

    server_type = models.CharField(
        null=True,
        blank=True,
        max_length=20
    )
    mount = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    class Meta(object):
        unique_together = (
            ("radio", "port"),
        )
