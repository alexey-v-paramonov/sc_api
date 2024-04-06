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
from radiotochka.billing import CUSTOM_PAYMENT_OPTIONS, RTBilling

class InvoiceRequestViewSet(viewsets.ModelViewSet):
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
        permissions.IsAuthenticated
    ]

    def get(self, request, format=None):

        return Response(CUSTOM_PAYMENT_OPTIONS)

class MonthTotalChargeView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, format=None):
        billing_instance = RTBilling()
        monthly = billing_instance.get_month_charge(self.request.user.email, self.request.user.id, True)
        return Response({
            "month_hosted": round(monthly[0], 2), 
            "month_du": round(monthly[1], 2),
            "month_self_hosted": round(monthly[2], 2), 
            "total": round(monthly[0] + monthly[1] + monthly[2], 2),
        })

class UserPaymentsView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, format=None):
        billing_instance = RTBilling()
        return Response({
            "payments": billing_instance.get_payment_history(self.request.user.id)
        })

class UserChargesView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, format=None):
        billing_instance = RTBilling()
        return Response({
            "charges": billing_instance.get_charge_history(self.request.user.id)
        })

invoice_request_router = routers.SimpleRouter()
invoice_request_router.register(
    r'invoice_request',
    InvoiceRequestViewSet,
    basename='invoice_request'
)
