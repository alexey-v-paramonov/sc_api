from django.urls import path

from radio.views import radio_service_router, ServersList
urlpatterns = radio_service_router.urls
urlpatterns += path(r'servers/', ServersList.as_view()),

