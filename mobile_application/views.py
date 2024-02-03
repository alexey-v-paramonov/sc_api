from django.shortcuts import render
from payments.models import InvoiceRequest
from rest_framework import (
    viewsets,
    permissions,
    routers
)
from mobile_application.serializers import AndroidApplicationSerializer, IosApplicationSerializer, AndroidApplicationRadioSerializer, IosApplicationRadioSerializer
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio

class AndroidApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = AndroidApplicationSerializer
    queryset = AndroidApplication.objects.all()

class IosApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = IosApplicationSerializer
    queryset = IosApplication.objects.all()


class AndroidApplicationRadioViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = AndroidApplicationRadioSerializer
    queryset = AndroidApplicationRadio.objects.all()


class IosApplicationRadioViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = IosApplicationRadioSerializer
    queryset = IosApplicationRadio.objects.all()

android_app_router = routers.SimpleRouter()
ios_app_router = routers.SimpleRouter()

android_radio_router = routers.SimpleRouter()
ios_radio_router = routers.SimpleRouter()

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

android_radio_router.register(
    r'android_radio',
    AndroidApplicationRadioViewSet,
    basename='android_radio'
)

ios_radio_router.register(
    r'ios_radio',
    IosApplicationRadioViewSet,
    basename='ios_radio'
)
