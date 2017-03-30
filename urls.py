from django.conf.urls import include, url
#from rest_framework_jwt.views import obtain_jwt_token
from users.views import obtain_jwt_token

urlpatterns = [
    url(r'^api/v1/api-token-auth/', obtain_jwt_token),
    url(r'^api/v1/',       include('users.urls')),
]
