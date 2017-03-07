from rest_framework import serializers

from users.models import User
from util.serializers import CustomErrorMessagesModelSerializer


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
        fields = ('password', 'username', 'email')
