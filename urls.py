from django.urls import include, path
from rest_framework.authtoken import views
from users.views import SCObtainAuthToken
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    # path('api/v1/api-token-auth/', views.obtain_auth_token),
    path('api/v1/api-token-auth/', SCObtainAuthToken.as_view()),
    path('api/v1/',       include('users.urls')),
    path('api/v1/',       include('radio.urls')),
    path('api/v1/',       include('voiceover.urls')),
    path('api/v1/',       include('payments.urls')),
    path('api/v1/',       include('mobile_application.urls')),
    path('api/v1/catalog/', include('catalog.urls')),
]
