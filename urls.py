from django.conf.urls import include, url
from users.views import obtain_jwt_token

urlpatterns = [
    url(r'^api/v1/api-token-auth/', obtain_jwt_token),
    url(r'^api/v1/',       include('users.urls')),
    url(r'^api/v1/',       include('radio.urls')),
]
