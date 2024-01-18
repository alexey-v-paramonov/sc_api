from rest_framework import serializers
from payments.models import InvoiceRequest


class InvoiceRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceRequest
        exclude = ('user', )
