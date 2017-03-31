from rest_framework import serializers
from radio.models import Radio
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)


class RadioSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = Radio
        exclude = ()
