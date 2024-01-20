from django.conf import settings
from django.core.mail import EmailMessage

from rest_framework import (
    viewsets,
    permissions,
    routers
)
from rest_framework.response import Response
from rest_framework import generics

from payments.models import InvoiceRequest
from payments.serializers import InvoiceRequestSerializer
from radiotochka.billing import CUSTOM_PAYMENT_OPTIONS
class HostedRadioViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = InvoiceRequestSerializer
    queryset = InvoiceRequest.objects.all()
    
    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        try:
            content = f"New invoice request from {self.request.user.email} to: {instance.email} amount: {instance.amount}"
            msg = EmailMessage(f"New Invoice request: {instance.email} - {instance.amount}$", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
            msg.send()
        except:
            pass

class CustomPaymentMethodsView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.AllowAny
    ]

    def get(self, request, format=None):

        return Response(CUSTOM_PAYMENT_OPTIONS)


invoice_request_router = routers.SimpleRouter()
invoice_request_router.register(
    r'invoice_request',
    HostedRadioViewSet,
    basename='invoice_request'
)
