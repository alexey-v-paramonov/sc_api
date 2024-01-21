from django.urls import path
from mobile_application.views import android_app_router, ios_app_router

urlpatterns = android_app_router.urls
urlpatterns += ios_app_router.urls

