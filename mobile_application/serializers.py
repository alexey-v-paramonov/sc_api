from rest_framework import serializers
from mobile_application.models import AndroidApplication, IosApplication


class AndroidApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = AndroidApplication
        exclude = ()

class IosApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = IosApplication
        exclude = ()
