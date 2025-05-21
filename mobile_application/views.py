from pyfcm import FCMNotification


from django.shortcuts import render
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When
from rest_framework import (
    viewsets,
    permissions,
    routers,
    status
)
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.conf import settings


from mobile_application.permissions import UserOwnsApp
from mobile_application.form_parsers import MultiPartJSONParser
from mobile_application.serializers import (
    AndroidApplicationSerializer,
    IosApplicationSerializer,
    AndroidApplicationRadioSerializer,
    IosApplicationRadioSerializer,
    AndroidRadioPrerollSerializer,
    IosRadioPrerollSerializer,
)
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio, AndroidRadioPreroll, iOsRadioPreroll




class AppBase:

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        
    @action(detail=True, methods=['put'])
    def set_radio_order(self, request, pk=None):
        ids = request.data
        id_to_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        self.radio_model.objects.filter(id__in=ids).update(order=id_to_order)
        return Response()

    @action(detail=True, methods=['patch'])
    def build(self, request, pk=None):
        app = self.get_object()
        app.schedule_build()

        template = get_template('email/app_build_requested.html')
        content = template.render({'app': app})
        msg = EmailMessage("New app build request", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
        msg.send()

        return Response()

class AndroidApplicationViewSet(AppBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
        # permissions.AllowAny,
    ]

    serializer_class = AndroidApplicationSerializer
    queryset = AndroidApplication.objects.all()
    radio_model = AndroidApplicationRadio

    @action(detail=True, methods=['post'])
    def send_push(self, request, pk=None):
        
        app = self.get_object()
        title = request.data.get('title')
        text = request.data.get('text')
        if not title or not text or not app.package_name:
            return Response(
                {"non_field_errors": "bad_params"},
                status=status.HTTP_400_BAD_REQUEST
            )
        message_payload = {
            "title": title,
            "message": text,
            "awake": "true"
            # "mutable_content": True
        }

        push_service = FCMNotification(service_account_file=settings.FCM_SERVICE_JSON_PATH, project_id=settings.FCM_PROJECT_ID)

        result = push_service.notify(
            topic_name=app.package_name,
            data_payload=message_payload,
        )

        return Response({"result": result})


class IosApplicationViewSet(AppBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
        # permissions.AllowAny,
    ]

    serializer_class = IosApplicationSerializer
    queryset = IosApplication.objects.all()
    radio_model = IosApplicationRadio
    @action(detail=True, methods=['post'])
    def send_push(self, request, pk=None):
        app = self.get_object()
        title = request.data.get('title')
        text = request.data.get('text')
        if not title or not text or not app.package_name:
            return Response(
                {"non_field_errors": "bad_params"},
                status=status.HTTP_400_BAD_REQUEST
            )

        push_service = FCMNotification(service_account_file=settings.FCM_SERVICE_JSON_PATH, project_id=settings.FCM_PROJECT_ID)

        result = push_service.notify(
            topic_name=f"{app.package_name}_ios",
            notification_title=title,
            notification_body=text,
            #sound="Default",
            #badge=1,
        )

        return Response({"result": result})

class AppRadioBase:

    def get_queryset(self):
        return self.queryset.filter(app_id=self.kwargs["app_id"], app__user=self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(app_id=self.kwargs["app_id"])
        instance.order = self.queryset.filter(app=instance.app).aggregate(Max('order'))['order__max'] + 1
        instance.save()
        return instance

class AndroidApplicationRadioViewSet(AppRadioBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        UserOwnsApp
        # permissions.AllowAny
    ]
    parser_classes = [MultiPartJSONParser]

    serializer_class = AndroidApplicationRadioSerializer
    queryset = AndroidApplicationRadio.objects.all()
    app_model = AndroidApplication


class IosApplicationRadioViewSet(AppRadioBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        UserOwnsApp
        # permissions.AllowAny
    ]
    parser_classes = [MultiPartJSONParser]

    serializer_class = IosApplicationRadioSerializer
    queryset = IosApplicationRadio.objects.all()
    app_model = IosApplication


class AndroidApplicationPrerollViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        UserOwnsApp
    ]
    parser_classes = [MultiPartJSONParser]

    serializer_class = AndroidRadioPrerollSerializer
    queryset = AndroidRadioPreroll.objects.all()
    app_model = AndroidApplication

    def get_queryset(self):
        return self.queryset.filter(radio__app_id=self.kwargs["app_id"], radio__app__user=self.request.user, radio_id=self.kwargs["radio_id"])


class IosApplicationPrerollViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        UserOwnsApp
    ]
    parser_classes = [MultiPartJSONParser]

    serializer_class = IosRadioPrerollSerializer
    queryset = iOsRadioPreroll.objects.all()
    app_model = IosApplication

    def get_queryset(self):
        return self.queryset.filter(radio__app_id=self.kwargs["app_id"], radio__app__user=self.request.user, radio_id=self.kwargs["radio_id"])


android_app_router = routers.SimpleRouter()
ios_app_router = routers.SimpleRouter()


android_app_router.register(
    r'android',
    AndroidApplicationViewSet,
    basename='android_app'
)

ios_app_router.register(
    r'ios',
    IosApplicationViewSet,
    basename='ios_app'
)

# Radios API
android_app_router.register(
    "android/(?P<app_id>[^/.]+)/radios",
    AndroidApplicationRadioViewSet,
    basename="android-app-radio",
)

ios_app_router.register(
    "ios/(?P<app_id>[^/.]+)/radios",
    IosApplicationRadioViewSet,
    basename="ios-app-radio",
)

# Prerolls API
android_app_router.register(
    "android/(?P<app_id>[^/.]+)/radios/(?P<radio_id>[^/.]+)/prerolls",
    AndroidApplicationPrerollViewSet,
    basename="android-app-prerolls",
)

ios_app_router.register(
    "ios/(?P<app_id>[^/.]+)/radios/(?P<radio_id>[^/.]+)/prerolls",
    IosApplicationPrerollViewSet,
    basename="ios-app-prerolls",
)
