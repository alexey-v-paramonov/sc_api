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

class AndroidApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = AndroidApplicationRadioChannel
        exclude = ()

class IosApplicationRadioChannelSerializer(CustomErrorMessagesModelSerializer):

    channels = AndroidApplicationRadioChannelSerializer(many=True, required=False)

    class Meta:
        model = IosApplicationRadioChannel
        exclude = ()

class AndroidApplicationRadioSerializer(CustomErrorMessagesModelSerializer):

    channels = AndroidApplicationRadioChannelSerializer(many=True, required=False)

    def create(self, validated_data):
        # print(dir(self))
        channels = validated_data.pop("channels")

        instance = self.Meta.model.objects.create(**validated_data)

        if instance:
            print("Channels: ", channels)
            for i, c in enumerate(channels):
                c['order'] = i
                c['radio_id'] = instance.id
                AndroidApplicationRadioChannel.objects.create(**c)
            # AndroidApplicationRadioChannel.objects.bulk_create(channels)


        return instance

    class Meta:
        model = AndroidApplicationRadio
        exclude = ()

class IosApplicationRadioSerializer(CustomErrorMessagesModelSerializer):

    channels = IosApplicationRadioChannelSerializer(many=True)    
    class Meta:
        model = IosApplicationRadio
        exclude = ()
