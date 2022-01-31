from rest_framework import serializers
# from rest_framework_jwt.serializers import JSONWebTokenSerializer
from users.models import User
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)


class UserSerializer(CustomErrorMessagesModelSerializer):

    password = serializers.CharField(
          write_only=True,
    )

    email = serializers.EmailField(
          required=True,
    )

    def create(self, validated_data):

        user = super(UserSerializer, self).create(validated_data)

        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()

        return user

    class Meta:
        model = User
        fields = ('password', 'username', 'email', 'id')


#class mJSONWebTokenSerializer(JSONWebTokenSerializer):
class mJSONWebTokenSerializer:

    def __init__(self, *args, **kwargs):

        super(mJSONWebTokenSerializer, self).__init__(*args, **kwargs)

        # Erors to codes
        for f in self.fields:
            self.fields[f].error_messages.update(
                (k, k) for k, v in self.fields[f].error_messages.items()
            )
