from django.urls import path
from payments.views import invoice_request_router, CustomPaymentMethodsView, MonthTotalChargeView

urlpatterns = invoice_request_router.urls
urlpatterns += path(r'custom_payment_methods/', CustomPaymentMethodsView.as_view()),
urlpatterns += path(r'month_total_charge/', MonthTotalChargeView.as_view()),


