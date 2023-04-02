from rest_framework import serializers
from users.models import User
from util.serializers import (
    CustomErrorMessagesModelSerializer,
)
from email_validator import EmailSyntaxError, EmailUndeliverableError, caching_resolver
from email_validator import validate_email


class UserSerializer(CustomErrorMessagesModelSerializer):

    password = serializers.CharField(
          write_only=True,
    )

    # email = serializers.EmailField(
    #       required=True,
    # )

    def create(self, validated_data):

        user = super(UserSerializer, self).create(validated_data)

        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()

        return user

    def validate_email(self, email):
        resolver = caching_resolver(timeout=5)

        try:
            valid = validate_email(email, dns_resolver=resolver)
        except EmailSyntaxError:
            raise serializers.ValidationError("syntax")
        except EmailUndeliverableError:
            raise serializers.ValidationError("undeliverable")
        # If email is correct - return normalized form
        return valid.email

    class Meta:
        model = User
        fields = ('password', 'username', 'email', 'id')

