from rest_framework import (
    viewsets,
    permissions,
    routers
)
from rest_framework.views import APIView
from rest_framework.response import Response

from radio.models import SelfHostedRadio, HostedRadio, RadioServer
from radio.serializers import SelfHostedRadioSerializer, HostedRadioSerializer, RadioServerSerializer
from radiotochka import billing


class ServersList(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, format=None):

        servers = RadioServer.objects.filter(
            available=True
        )
        serializer = RadioServerSerializer(servers, many=True)
        return Response(serializer.data)


class PricingView(APIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def get(self, request):
        bitrate = request.query_params.get('bitrate', None)
        listeners = request.query_params.get('listeners', None)
        disk_quota = request.query_params.get('disk_quota', None)
        if not all([bitrate, listeners, disk_quota]):
            return Response({
                "error": "missing_params"
            }, status=400)

        try:
            bitrate = int(bitrate)
            listeners = int(listeners)
            disk_quota = int(disk_quota)
        except ValueError:
            return Response({
                "error": "invalid_params"
            }, status=400)

        billing_instance = billing.RTBilling()
        traffic_price  =  billing_instance.calc_price(bitrate, listeners)
        du_price = billing_instance.get_du_price(disk_quota)
        return Response({
            "price": traffic_price,
            "du_price": du_price
        })


class HostedRadioViewSet(viewsets.ModelViewSet):

    #permission_classes = [
    #    permissions.IsAuthenticated
    #]

    serializer_class = HostedRadioSerializer
    queryset = HostedRadio.objects.all()

class SelfHostedRadioViewSet(viewsets.ModelViewSet):

    #permission_classes = [
    #    permissions.IsAuthenticated
    #]

    serializer_class = SelfHostedRadioSerializer
    queryset = SelfHostedRadio.objects.all()

hosted_radio_service_router = routers.SimpleRouter()
hosted_radio_service_router.register(
    r'hosted_radio',
    HostedRadioViewSet,
    basename='hosted_radio'
)

self_hosted_radio_service_router = routers.SimpleRouter()
self_hosted_radio_service_router.register(
    r'self_hosted_radio',
    SelfHostedRadioViewSet,
    basename='self_hosted_radio'
)
