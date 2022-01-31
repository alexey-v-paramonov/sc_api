
from django.urls import path

from users.views import Users

urlpatterns = [
    path(r'users/<int:pk>/', Users.as_view()),
    path(r'users/', Users.as_view()),
]
