from rest_framework import serializers
from radio.models import Radio, RadioServer
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)

class RadioServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = RadioServer
        exclude = ()


class RadioSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = Radio
        exclude = ()
