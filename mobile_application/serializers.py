from rest_framework import serializers
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio, AndroidApplicationRadioChannel, IosApplicationRadioChannel

from util.serializers import (
    CustomErrorMessagesModelSerializer,
)


class AndroidApplicationSerializer(CustomErrorMessagesModelSerializer):

    missing_parts = serializers.SerializerMethodField(read_only=True)

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


class IosApplicationSerializer(CustomErrorMessagesModelSerializer):

    missing_parts = serializers.SerializerMethodField(read_only=True)

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

class AndroidApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):
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
