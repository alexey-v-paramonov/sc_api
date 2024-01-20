from django.urls import path
from payments.views import invoice_request_router, CustomPaymentMethodsView

urlpatterns = invoice_request_router.urls
urlpatterns += path(r'custom_payment_methods/', CustomPaymentMethodsView.as_view()),

