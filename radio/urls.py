from django.urls import path

from radio.views import self_hosted_radio_service_router, hosted_radio_service_router, ServersList, PricingView
urlpatterns = hosted_radio_service_router.urls
urlpatterns += self_hosted_radio_service_router.urls
urlpatterns += path(r'servers/', ServersList.as_view()),
urlpatterns += path(r'pricing/', PricingView.as_view()),

