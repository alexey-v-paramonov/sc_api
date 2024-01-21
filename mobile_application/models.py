from django.db import models
from django.conf import settings
from radio.models import AudioFormat


class AppStatus:

    DEFAULT = 0
    QUEUED = 1
    DONE = 2
    ERROR = 3
    # Archieved?

    choices = (
        (DEFAULT, 'Default'),
        (QUEUED, 'Queued to build'),
        (DONE, 'Done'),
        (ERROR, 'Build error'),
    )


class CopyrightType:

    SC = 0
    WHITELABEL = 1
    CUSTOM = 2

    choices = (
        (SC, 'Streaming.center'),
        (WHITELABEL, 'Whitelabel'),
        (CUSTOM, 'Custom'),
    )


class ServerType:

    SHOUTCAST = 0
    ICECAST = 1

    choices = (
        (SHOUTCAST, 'Shoutcast'),
        (ICECAST, 'Icecast'),
    )

class BaseApplication(models.Model):

    title = models.CharField(
        "Application title",
        null=False,
        blank=False,
        max_length=30
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Owner",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

    description = models.TextField(null=False, blank=False)
    website_url = models.URLField(null=True, blank=True)
    email = models.EmailField(null=False, blank=False)

    is_paid = models.BooleanField(
        default=False,
    )

    version = models.PositiveIntegerField(
        null=False,
        blank=True,
        default=1,
    )
    
    yandex_appmetrica_key = models.CharField(
        null=True,
        blank=True,
        max_length=255
    )

    status = models.PositiveSmallIntegerField(
        "Status",
        null=False,
        blank=True,
        choices=AppStatus.choices,
        default=AppStatus.DEFAULT,
    )

    # Colors
    tabs_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#161616"
    )
    tabs_icon_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#dadada"
    )
    tabs_icon_selected_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#ff9500"
    )
    main_theme_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#333333"
    )
    text_secondary_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#333333"
    )
    play_button_border_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#8f8e94"
    )
    volume_buttons_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#333333"
    )
    volume_bar_active_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#333333"
    )
    volume_bar_inactive_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#dddddd"
    )
    bg_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#f2f2f2"
    )
    bg_color_gradient = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#f2f2f2"
    )
    font_color = models.CharField(
        null=False,
        blank=False,
        max_length=20,
        default="#000000"
    )

    enable_push = models.BooleanField(
        default=False,
    )

    fcm_api_key = models.CharField(
        null=True,
        blank=True,
        max_length=255
    )

    # Copyright
    copyright_type = models.PositiveSmallIntegerField(
        "Copyright",
        null=False,
        blank=True,
        choices=CopyrightType.choices,
        default=CopyrightType.SC,
    )

    copyright_title = models.CharField(
        null=True,
        blank=True,
        max_length=255
    )
    copyright_url = models.CharField(
        null=True,
        blank=True,
        max_length=255
    )

    is_sc_publishing = models.BooleanField(
        default=True,
    )

    store_url = models.URLField(null=True, blank=True)

    display_timer = models.BooleanField(
        default=True,
    )

    class Meta(object):
        abstract = True

class AndroidApplication(BaseApplication):

    description_short  = models.CharField(
        null=False,
        blank=False,
        max_length=80
    )

class IosApplication(BaseApplication):

    keywords = models.CharField(
        null=True,
        blank=True,
        max_length=100
    )

class ApplicationRadioBase(models.Model):

    title = models.CharField(
        null=False,
        blank=False,
        max_length=255
    )

    description = models.TextField(null=False, blank=False)
    logo = models.FileField(
        "Logo",
    )
    sc_api_url = models.URLField(null=True, blank=True)
    sc_server_id = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    allow_shoutbox =  models.BooleanField(
        default=True,
    )
    allow_likes =  models.BooleanField(
        default=True,
    )
    allow_dislikes = models.BooleanField(
        default=True,
    )
    allow_website_url = models.BooleanField(
        default=True,
    )
    hide_metadata =  models.BooleanField(
        default=True,
    )

    order = models.PositiveSmallIntegerField(
        null=False,
        blank=False,
        default=0
    )

    class Meta(object):
        abstract = True


class AndroidApplicationRadio(ApplicationRadioBase):

    app = models.ForeignKey(
        AndroidApplication,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

class IosApplicationRadio(ApplicationRadioBase):
    app = models.ForeignKey(
        IosApplication,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )


class ApplicationRadioChannelBase(models.Model):

    stream_url = models.URLField(null=False, blank=False)
    stream_url_fallback = models.URLField(null=True, blank=True)
    bitrate = models.PositiveSmallIntegerField(
        null=False,
        blank=True,
        default=128,
    )
    audio_format = models.PositiveSmallIntegerField(
        "Audio format",
        choices=AudioFormat.choices,
        blank=False,
        null=False,
        default=AudioFormat.MP3,
    )

    server_type = models.PositiveSmallIntegerField(
        "Server type",
        choices=ServerType.choices,
        blank=False,
        null=False,
        default=ServerType.SHOUTCAST,
    )
    order = models.PositiveSmallIntegerField(
        null=False,
        blank=False,
        default=0
    )

    class Meta(object):
        abstract = True

class AndroidApplicationRadioChannel(ApplicationRadioChannelBase):

    radio = models.ForeignKey(
        AndroidApplicationRadio,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

class IosApplicationRadioChannel(ApplicationRadioChannelBase):

    radio = models.ForeignKey(
        IosApplicationRadio,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )
