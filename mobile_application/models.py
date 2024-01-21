from django.db import models
from django.conf import settings


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

    # status
    #+ Archive

    # Colors
    tabs_color
    tabs_icon_color
    tabs_icon_selected_color
    main_theme_color
    text_secondary_color
    play_button_border_color
    volume_buttons_color
    volume_bar_active_color
    volume_bar_inactive_color
    bg_color
    bg_color_gradient
    font_color

    enable_push = models.BooleanField(
        default=False,
    )

    fcm_api_key = models.CharField(
        null=True,
        blank=True,
        max_length=255
    )
    #
    # copyright_type - own, custom, none
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

class AndroidApplicationRadioChannel(models.Model):

    radio = models.ForeignKey(
        AndroidApplicationRadio,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

class IosApplicationRadioChannel(models.Model):

    radio = models.ForeignKey(
        IosApplicationRadio,
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )
