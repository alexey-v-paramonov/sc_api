from rest_framework import serializers
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio, AndroidApplicationRadioChannel, IosApplicationRadioChannel

from util.serializers import (
    CustomErrorMessagesModelSerializer,
)


class AndroidApplicationSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = AndroidApplication
        exclude = ()

class IosApplicationSerializer(CustomErrorMessagesModelSerializer):
    class Meta:
        model = IosApplication
        exclude = ()
        extra_kwargs = {"radio": {"required": False, "allow_null": True}}

class AndroidApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):
    class Meta:
        model = AndroidApplicationRadioChannel
        exclude = ()
        extra_kwargs = {"radio": {"required": False, "allow_null": True}}

class IosApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):

    channels = AndroidApplicationRadioChannelSerializer(many=True, required=False)

    class Meta:
        model = IosApplicationRadioChannel
        exclude = ()
        

class AndroidApplicationRadioSerializer(CustomErrorMessagesModelSerializer):

    channels = AndroidApplicationRadioChannelSerializer(many=True)

    def create(self, validated_data):

        channels = validated_data.pop("channels")
        instance = self.Meta.model.objects.create(**validated_data)

        if instance:
            for i, c in enumerate(channels):
                c['order'] = i
                c['radio_id'] = instance.id
                AndroidApplicationRadioChannel.objects.create(**c)
        return instance

    class Meta:
        model = AndroidApplicationRadio
        exclude = ()


class IosApplicationRadioSerializer(CustomErrorMessagesModelSerializer):

    channels = IosApplicationRadioChannelSerializer(many=True)    
    class Meta:
        model = IosApplicationRadio
        exclude = ()
