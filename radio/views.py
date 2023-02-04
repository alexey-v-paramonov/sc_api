from rest_framework import (
    viewsets,
    permissions,
    routers
)
from rest_framework.views import APIView
from rest_framework.response import Response

from radio.models import HostedRadio, RadioServer
from radio.serializers import HostedRadioSerializer, RadioServerSerializer


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


class HostedRadioViewSet(viewsets.ModelViewSet):

    #permission_classes = [
    #    permissions.IsAuthenticated
    #]

    serializer_class = HostedRadioSerializer
    queryset = HostedRadio.objects.all()

radio_service_router = routers.SimpleRouter()
radio_service_router.register(
    r'hosted_radio',
    HostedRadioViewSet,
    basename='radio_service'
)
