from rest_framework import serializers
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio

from util.serializers import (
    CustomErrorMessagesModelSerializer,
)

class AndroidApplicationRadioSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = AndroidApplicationRadio
        exclude = ()

class IosApplicationRadioSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = IosApplicationRadio
        exclude = ()

class AndroidApplicationSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = AndroidApplication
        exclude = ()

class IosApplicationSerializer(CustomErrorMessagesModelSerializer):

    class Meta:
        model = IosApplication
        exclude = ()
