from rest_framework import (
    viewsets,
    permissions,
    routers
)
from rest_framework.views import APIView
from rest_framework.response import Response

from radio.models import Radio, RadioServer
from radio.serializers import RadioSerializer, RadioServerSerializer


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


class RadioServiceViewSet(viewsets.ModelViewSet):

    #permission_classes = [
    #    permissions.IsAuthenticated
    #]

    serializer_class = RadioSerializer
    queryset = Radio.objects.all()

radio_service_router = routers.SimpleRouter()
radio_service_router.register(
    r'radio_service',
    RadioServiceViewSet,
    basename='radio_service'
)
