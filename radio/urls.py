from django.conf.urls import url

from radio.views import radio_service_router, ServersList
urlpatterns = radio_service_router.urls
urlpatterns += url(r'^servers/$', ServersList.as_view()),

