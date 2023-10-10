from django.urls import path

from radio.views import radio_service_router, ServersList, PricingView
urlpatterns = radio_service_router.urls
urlpatterns += path(r'servers/', ServersList.as_view()),
urlpatterns += path(r'pricing/', PricingView.as_view()),

