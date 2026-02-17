import logging
from configparser import ConfigParser


from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.decorators import action

from django.contrib.auth.tokens import default_token_generator
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


from users.serializers import UserSerializer, PasswordResetConfirmSerializer, UserSettingsSerializer
from users.models import User, EmailConfirmationToken
from rest_framework import viewsets
from rest_framework import routers
from radio.models import HostedRadio, RadioServer, AudioFormat, CopyrightType


logger = logging.getLogger('django')

class UsersView(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_permissions(self):
        # Special case for signup
        if self.request.method == 'POST':
            self.permission_classes = (permissions.AllowAny,)

        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def request_account_deletion(self, request, pk=None):
        user = self.get_object()
        EmailMessage("User requested to delete his account", f"User: {user.email}", settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,]).send()
        return Response()


    @action(detail=True, methods=['put'])
    def profile(self, request, pk=None):
        serializer = UserSettingsSerializer(data=request.data, instance=self.get_object())
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response()


class SCObtainAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"non_field_errors": "bad_credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'id': user.id, 'email': user.email})
    
class PasswordResetView(APIView):

    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        email = request.data.get("email", "").strip()
        lang = request.data.get("lang", "en").strip()
        if email:
            try:
                user = User.objects.get(email__iexact=email, is_superuser=False)
            except User.DoesNotExist:
                return Response(
                    {
                        "email": [
                            "user_not_found",
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            domain = "streaming.center"
            template = "email/password_reset_en.html"
            subject = "Reset your Streaming.center password"
            if lang == "ru":
                domain = "radio-tochka.com"
                template = "email/password_reset_ru.html"
                subject = "Сброс пароля Radio-Tochka.com"

            ctx = {
                "user": user,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
                "domain": domain
            }
            template = get_template(template)
            content = template.render(ctx)
            text_content = strip_tags(content)
            if lang == "ru":            
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

            return Response({})

        return Response({"email": "required"}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(pk=serializer.data['uid'])
            user.set_password(serializer.data["password"].strip())
            user.save()
            return Response({})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class EmailConfirmationView(View):
    """
    Two-step email confirmation to prevent automatic confirmation by email scanners.
    GET: Shows confirmation prompt page with button
    POST: Actually performs the confirmation and creates HostedRadio
    
    Note: CSRF exempt because this is accessed via email link from external context.
    The token itself provides security (cryptographically secure UUID, single-use, user-specific).
    """

    def get(self, request):
        """Show confirmation prompt page - does NOT auto-confirm"""
        token = request.GET.get("token", "").strip()
        
        # Detect language early
        host = request.get_host().lower()
        is_ru_domain = "radio-tochka.com" in host
        failed_template = "email_confirmation_failed_ru.html" if is_ru_domain else "email_confirmation_failed_en.html"
        prompt_template = "email_confirmation_prompt_ru.html" if is_ru_domain else "email_confirmation_prompt_en.html"
        
        if not token:
            return render(request, failed_template)
        
        # Validate token exists
        try:
            EmailConfirmationToken.objects.get(token=token)
        except (EmailConfirmationToken.DoesNotExist, ValueError):
            return render(request, failed_template)
        
        # Show prompt page with confirmation button
        return render(request, prompt_template, {"token": token})

    def post(self, request):
        """Actually perform the confirmation after user clicks button"""
        token = request.POST.get("token", "").strip()
        
        # Detect language
        host = request.get_host().lower()
        is_ru_domain = "radio-tochka.com" in host
        failed_template = "email_confirmation_failed_ru.html" if is_ru_domain else "email_confirmation_failed_en.html"
        
        if not token:
            return render(request, failed_template)
        
        try:
            confirmation_token = EmailConfirmationToken.objects.get(token=token)
        except (EmailConfirmationToken.DoesNotExist, ValueError):
            return render(request, failed_template)
        
        user = confirmation_token.user
        
        # Check if email is already confirmed
        if user.email_confirmed:
            # Already confirmed - just show success
            pass
        else:
            # Confirm email
            user.email_confirmed = True
            user.save()
            
            # Create HostedRadio for demo account
            if not HostedRadio.objects.filter(user=user).exists():
                HARDCODED_CONFIG_PATH = "/opt/bin/utils.ini"
                cp = ConfigParser()
                cp.read(HARDCODED_CONFIG_PATH)               
                hostip = cp.get("Server", "HOST_IP")
                server = RadioServer.objects.get(ip=hostip)
                HostedRadio.objects.create(
                    user=user,
                    server=server,
                    login=f"radio{user.id}",
                    initial_audio_format=AudioFormat.MP3,
                    initial_bitrate=128,
                    initial_listeners=5,
                    initial_du=5,
                    copyright_type=CopyrightType.TEST,
                    is_demo=True,
                )
            
            logger.info("Email confirmed for user: %s, HostedRadio created", user.email)
            
            # Delete the token after successful confirmation
            confirmation_token.delete()
        
        # Prepare context for success page
        domain = "streaming.center"
        title = "Email Confirmed!"
        message = "Your email has been successfully confirmed. Your free trial demo radio station will be created within 5 minutes and the credentials will be sent to your email."
        button_text = "Login to Dashboard"
        
        if user.is_russian():
            domain = "radio-tochka.com"
            title = "Email Подтвержден!"
            message = "Ваш email был успешно подтвержден. Ваша бесплатная пробная демо радиостанция будет создана в течение 5 минут, и учетные данные будут отправлены на ваш email."
            button_text = "Войти в личный кабинет"
        
        context = {
            "title": title,
            "message": message,
            "button_text": button_text,
            "domain": domain
        }
        
        return render(request, "email_confirmation_success.html", context)


users_router = routers.SimpleRouter()
users_router.register(r"users", UsersView)
