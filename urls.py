from django.urls import include, path
# from users.views import obtain_jwt_token

urlpatterns = [
    # path('api/v1/api-token-auth/', obtain_jwt_token),
    path('api/v1/',       include('users.urls')),
    path('api/v1/',       include('radio.urls')),
]
