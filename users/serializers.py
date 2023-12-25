from rest_framework import serializers
from users.models import User
from util.serializers import (
    CustomErrorMessagesModelSerializer,
    CustomErrorMessagesSerializer
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from email_validator import EmailSyntaxError, EmailUndeliverableError, caching_resolver
from email_validator import validate_email
from rest_framework.authtoken.models import Token


class UserSerializer(CustomErrorMessagesModelSerializer):

    password = serializers.CharField(
          write_only=True,
    )
    token = serializers.SerializerMethodField(read_only=True)

    def get_token(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return token.key

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
        fields = ('password', 'email', 'id', 'token', 'language', 'currency', 'balance', 'agreement_accepted')

class PasswordResetConfirmSerializer(CustomErrorMessagesSerializer):

    """
    Serializer for updating a password with a token.
    """

    password = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate_uid(self, value):

        try:
            uid = urlsafe_base64_decode(value).decode()
            User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("user_not_found")

        return uid

    def validate(self, data):
        uid = data["uid"]
        token = data["token"]
        user = User.objects.get(pk=uid)
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError("token_invalid")

        return data
