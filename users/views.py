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
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


from users.serializers import UserSerializer, PasswordResetConfirmSerializer, UserSettingsSerializer
from users.models import User
from rest_framework import viewsets
from rest_framework import routers

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

    @action(detail=True, methods=['put'])
    def profile(self, request, pk=None):

        serializer = UserSettingsSerializer(data=request.data)
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
            msg = EmailMultiAlternatives(subject, text_content, settings.ADMIN_EMAIL, [user.email,])
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

users_router = routers.SimpleRouter()
users_router.register(r"users", UsersView)
