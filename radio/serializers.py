from rest_framework import serializers
from radio.models import HostedRadio, RadioServer
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
