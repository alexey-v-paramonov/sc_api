from django.shortcuts import render
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
import json

from mobile_application.permissions import UserOwnsApp
from rest_framework import (
    viewsets,
    permissions,
    routers
)
from mobile_application.serializers import AndroidApplicationSerializer, IosApplicationSerializer, AndroidApplicationRadioSerializer, IosApplicationRadioSerializer
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio


class AppBase:

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
        
    @action(detail=True, methods=['put'])
    def set_radio_order(self, request, pk=None):
        ids = request.data
        id_to_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        self.radio_model.objects.filter(id__in=ids).update(order=id_to_order)
        return Response()

class AndroidApplicationViewSet(AppBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
        # permissions.AllowAny,
    ]

    serializer_class = AndroidApplicationSerializer
    queryset = AndroidApplication.objects.all()
    radio_model = AndroidApplicationRadio


class IosApplicationViewSet(AppBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
        # permissions.AllowAny,
    ]

    serializer_class = IosApplicationSerializer
    queryset = IosApplication.objects.all()
    radio_model = IosApplicationRadio

class AppRadioBase:

    def get_queryset(self):
        return self.queryset.filter(app_id=self.kwargs["app_id"])

    def perform_create(self, serializer):
        channels_json = json.loads(self.request.data['channels'])
        instance = serializer.save(app_id=self.kwargs["app_id"], channels=channels_json)
        instance.order = self.queryset.filter(app=instance.app).aggregate(Max('order'))['order__max'] + 1
        instance.save()
        return instance

class AndroidApplicationRadioViewSet(AppRadioBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        UserOwnsApp
        # permissions.AllowAny
    ]

    serializer_class = AndroidApplicationRadioSerializer
    queryset = AndroidApplicationRadio.objects.all()
    app_model = AndroidApplication


class IosApplicationRadioViewSet(AppRadioBase, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated,
        UserOwnsApp
        # permissions.AllowAny
    ]

    serializer_class = IosApplicationRadioSerializer
    queryset = IosApplicationRadio.objects.all()
    app_model = IosApplication


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
android_app_router.register(
    "android/(?P<app_id>[^/.]+)/radios",
    AndroidApplicationRadioViewSet,
    basename="android-app-radio",
)

android_app_router.register(
    "ios/(?P<app_id>[^/.]+)/radios",
    IosApplicationRadioViewSet,
    basename="ios-app-radio",
)
