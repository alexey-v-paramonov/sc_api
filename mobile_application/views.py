from django.shortcuts import render
from django.db.models import Max
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Case, When


from payments.models import InvoiceRequest
from rest_framework import (
    viewsets,
    permissions,
    routers
)
from mobile_application.serializers import AndroidApplicationSerializer, IosApplicationSerializer, AndroidApplicationRadioSerializer, IosApplicationRadioSerializer
from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio


class UpdateRadioOrder:
    @action(detail=True, methods=['put'])
    def set_radio_order(self, request, pk=None):
        ids = request.data
        id_to_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        self.radio_model.objects.filter(id__in=ids).update(order=id_to_order)
        return Response()

class AndroidApplicationViewSet(UpdateRadioOrder, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = AndroidApplicationSerializer
    queryset = AndroidApplication.objects.all()
    radio_model = AndroidApplicationRadio


class IosApplicationViewSet(UpdateRadioOrder, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = IosApplicationSerializer
    queryset = IosApplication.objects.all()
    radio_model = IosApplicationRadio

class SetOrderOnCreate:
    def perform_create(self, serializer):
        instance = serializer.save()
        instance.order = self.queryset.filter(app=instance.app).aggregate(Max('order'))['order__max'] + 1
        instance.save()
        return instance

class AndroidApplicationRadioViewSet(SetOrderOnCreate, viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = AndroidApplicationRadioSerializer
    queryset = AndroidApplicationRadio.objects.all()

class IosApplicationRadioViewSet(SetOrderOnCreate, viewsets.ModelViewSet):
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
    r'radio/android',
    AndroidApplicationRadioViewSet,
    basename='android_radio'
)

ios_radio_router.register(
    r'radio/ios',
    IosApplicationRadioViewSet,
    basename='ios_radio'
)
