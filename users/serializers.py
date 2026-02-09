import random
import logging

from time import time
from rest_framework import serializers
from users.models import User, EmailConfirmationToken
from util.serializers import (
    CustomErrorMessagesModelSerializer,
    CustomErrorMessagesSerializer
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from email_validator import EmailSyntaxError, EmailUndeliverableError, caching_resolver
from email_validator import validate_email
from rest_framework.authtoken.models import Token
from rest_framework.validators import UniqueValidator
from django.template.loader import get_template
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from ipware import get_client_ip
from ipwhois import IPWhois

logger = logging.getLogger('django')

class EmailValidatiorBase:

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

class UserSettingsSerializer(CustomErrorMessagesModelSerializer, EmailValidatiorBase):

    email = serializers.EmailField(required=False, validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(required=False)

    def validate_password(self, password):
        if password and len(password) < 8:
            raise serializers.ValidationError("length")
        return password

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)
    
    class Meta:
        model = User
        fields = ('password', 'email', 'subscribed')

class UserSerializer(CustomErrorMessagesModelSerializer, EmailValidatiorBase):

    password = serializers.CharField(
          write_only=True, required=False
    )
    token = serializers.SerializerMethodField(read_only=True)
    balance = serializers.SerializerMethodField()

    def get_balance(self, user):
        return round(float(user.balance), 2)

    def get_token(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return token.key

    def create(self, validated_data):
        client_ip, _ = get_client_ip(self.context["request"])
        logger.info("Create user request IP: %s", client_ip)
        if client_ip is not None:
            whois = IPWhois(client_ip)
            results = whois.lookup_rdap()
            asn_description = results.get("asn_description", "")
            logger.info("Create user Whois: %s", asn_description)
            if asn_description.lower().find("vdsina") >= 0:
                raise serializers.ValidationError("ip_invalid")

        user = super(UserSerializer, self).create(validated_data)

        if 'password' in validated_data:
            # User with password: regular registration
            user.set_password(validated_data['password'])
            user.email_confirmed = True  # Assume confirmed for regular registration
            user.save()
            logger.info("User created, IP: %s", client_ip)
            
            template = "email/registration/reg_en.html"
            subject = "Welcome to Streaming.center!"
            if user.is_russian():
                template = "email/registration/reg_ru.html"
                subject = "Добро пожаловать на Radio-Tochka.com!"

            template = get_template(template)
            content = template.render(validated_data)
            text_content = strip_tags(content)
            if user.is_russian():        
                msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [user.email,])
            else:
                with get_connection(
                    host=settings.SC_EMAIL_HOST,
                    port=settings.SC_EMAIL_PORT,
                    username=settings.SC_EMAIL_HOST_USER,
                    password=settings.SC_EMAIL_HOST_PASSWORD,
                    use_ssl=settings.SC_EMAIL_USE_SSL,
                    use_tls=settings.SC_EMAIL_USE_TLS,
                ) as connection:
                    msg = EmailMultiAlternatives(subject, text_content, settings.SC_ADMIN_EMAIL, [user.email,], connection=connection)
                
            msg.attach_alternative(content, "text/html")
            msg.send()
        else:
            # No password: demo account - generate password and send confirmation email
            passstr = "qwertyuiopasdfghjkzxcvbnmQWERTYUIPASDFGHJKLZXCVBNM234567890"
            random.seed(time())
            pwd = ""
            for i in range(0, 12):
                c = random.randint(0, len(passstr) - 1)
                pwd = pwd + passstr[c]
            user.set_password(pwd)
            user.email_confirmed = False  # Email not confirmed yet
            user.save()
            validated_data['password'] = pwd
            
            # Create confirmation token
            confirmation_token = EmailConfirmationToken.objects.create(user=user)
            
            # Send confirmation email
            domain = "streaming.center"
            template = "email/email_confirmation_en.html"
            subject = "Confirm your email - Streaming.center"
            if user.is_russian():
                domain = "radio-tochka.com"
                template = "email/email_confirmation_ru.html"
                subject = "Подтвердите email - Radio-Tochka.com"
            
            ctx = {
                "user": user,
                "token": confirmation_token.token,
                "domain": domain,
                "password": pwd
            }
            template = get_template(template)
            content = template.render(ctx)
            text_content = strip_tags(content)
            if user.is_russian():        
                msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [user.email,])
            else:
                with get_connection(
                    host=settings.SC_EMAIL_HOST,
                    port=settings.SC_EMAIL_PORT,
                    username=settings.SC_EMAIL_HOST_USER,
                    password=settings.SC_EMAIL_HOST_PASSWORD,
                    use_ssl=settings.SC_EMAIL_USE_SSL,
                    use_tls=settings.SC_EMAIL_USE_TLS,
                ) as connection:
                    msg = EmailMultiAlternatives(subject, text_content, settings.SC_ADMIN_EMAIL, [user.email,], connection=connection)
                
            msg.attach_alternative(content, "text/html")
            msg.send()
            logger.info("Demo user created, IP: %s, waiting for email confirmation", client_ip)

        return user
    
    class Meta:
        model = User
        fields = ('password', 'email', 'id', 'token', 'language', 'currency', 'balance', 'agreement_accepted', 'subscribed')

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
