from rest_framework import (
    viewsets,
    permissions,
    routers
)

from radio.models import Radio
from radio.serializers import RadioSerializer

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
    base_name='radio_service'
)
