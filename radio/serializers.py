from rest_framework import serializers
from radio.models import SelfHostedRadio, HostedRadio, RadioServer
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)

class RadioServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = RadioServer
        exclude = ()


class HostedRadioSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = HostedRadio
        exclude = ()

class SelfHostedRadioSerializer(CustomErrorMessagesModelSerializer):

    def validate_ip(self, ip):
        raise serializers.ValidationError("syntax")

    class Meta:
        model = SelfHostedRadio
        exclude = ()
