import pathlib
from urllib.parse import urlparse
from PIL import Image
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio, AndroidApplicationRadioChannel, IosApplicationRadioChannel, ServerType

from util.serializers import (
    CustomErrorMessagesModelSerializer,
)

print(dir(serializers))
class ApplicationBaseSerializer(CustomErrorMessagesModelSerializer):
    build_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    price = serializers.IntegerField(read_only=True)

    def validate_allow_website_url(self, _):
        # Parse formData boolean value
        return self.initial_data.get('allow_website_url', "true") == 'true'

    def validate_icon(self, i):
        try:
            im = Image.open(i)
        except:
            raise ValidationError("image_is_not_png")

        if im.format != 'PNG':
            raise ValidationError("image_is_not_png")
        return i

    def validate_logo(self, i):

        try:
            im = Image.open(i)
        except:
            raise ValidationError("image_is_not_png")

        if im.format != 'PNG':
            raise ValidationError("image_is_not_png")

        return i

class AndroidApplicationSerializer(ApplicationBaseSerializer):

    missing_parts = serializers.SerializerMethodField(read_only=True)
    short_package_name = serializers.SerializerMethodField(read_only=True)
    test_days_left = serializers.SerializerMethodField(read_only=True)

    def get_test_days_left(self, app):
        if app.is_paid:
            return 0
        return 5 - min( abs((app.created - timezone.now()).days + 1), 5)

    def get_short_package_name(self, app):
        if not app.package_name:
            return None
        return app.package_name.replace("ua.radio.", "").replace("center.streaming.", "")

    def get_missing_parts(self, app):
        missing_parts = []
        if not app.title or not app.icon or not app.logo or not app.description or not app.email or not app.website_url:
            missing_parts.append('info')

        if app.androidapplicationradio_set.count() == 0:
            missing_parts.append('radio')

        if not app.is_paid and app.user.balance < app.price:
            missing_parts.append('payment')
        return missing_parts


    class Meta:
        model = AndroidApplication
        exclude = ()
        read_only_fields = (
            "is_paid",
            "price",
        )


class IosApplicationSerializer(ApplicationBaseSerializer):

    missing_parts = serializers.SerializerMethodField(read_only=True)
    test_days_left = serializers.SerializerMethodField(read_only=True)

    def get_test_days_left(self, app):
        return 0

    def validate_icon(self, i):
        try:
            im = Image.open(i)
        except:
            raise ValidationError("image_is_not_png")

        if im.mode == 'RGBA':
            raise ValidationError("png_is_transparent")

        return super().validate_icon(i)

    def get_missing_parts(self, app):
        missing_parts = []
        if not app.title or not app.icon or not app.logo or not app.description or not app.email or not app.website_url:
            missing_parts.append('info')

        if app.iosapplicationradio_set.count() == 0:
            missing_parts.append('radio')

        if not app.is_paid and app.user.balance < app.price:
            missing_parts.append('payment')
        return missing_parts

    class Meta:
        model = IosApplication
        exclude = ()
        read_only_fields = (
            "is_paid",
            "price",
        )

class AndroidApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):

    def validate(self, data):
        server_type = data.get('server_type', None)
        stream_url = data.get('stream_url', None)

        if stream_url and server_type == ServerType.HLS:
            path = urlparse(stream_url).path
            extension = pathlib.Path(path).suffix.lower()
            if extension != ".m3u8":
                raise ValidationError("hls_not_m3u8")

        return data

    class Meta:
        model = AndroidApplicationRadioChannel
        exclude = ()
        extra_kwargs = {"radio": {"required": False, "allow_null": True}}


class IosApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):

    channels = AndroidApplicationRadioChannelSerializer(
        many=True, required=False)

    class Meta:
        model = IosApplicationRadioChannel
        exclude = ()
        extra_kwargs = {"radio": {"required": False, "allow_null": True}}


class ApplicationRadioSerializerBase:
    def create(self, validated_data):

        channels = validated_data.pop("channels")
        instance = self.Meta.model.objects.create(**validated_data)

        if instance:
            for i, c in enumerate(channels):
                c['order'] = i
                c['radio_id'] = instance.id
                self.Meta.model_channels.objects.create(**c)
        return instance

    def update(self, radio, validated_data):
        channels = validated_data.pop("channels")
        super().update(radio, validated_data)

        radio.channels.all().delete()
        for i, c in enumerate(channels):
            c['order'] = i
            c['radio_id'] = radio.id
            self.Meta.model_channels.objects.create(**c)
        return radio


class AndroidApplicationRadioSerializer(ApplicationRadioSerializerBase, CustomErrorMessagesModelSerializer):

    channels = AndroidApplicationRadioChannelSerializer(many=True)

    class Meta:
        model = AndroidApplicationRadio
        model_channels = AndroidApplicationRadioChannel
        exclude = ()


class IosApplicationRadioSerializer(ApplicationRadioSerializerBase, CustomErrorMessagesModelSerializer):

    channels = IosApplicationRadioChannelSerializer(many=True)

    class Meta:
        model = IosApplicationRadio
        model_channels = IosApplicationRadioChannel
        exclude = ()
