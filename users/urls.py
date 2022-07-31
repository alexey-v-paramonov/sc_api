
from django.urls import path

from users.views import users_router
#UsersView

urlpatterns = users_router.urls

# urlpatterns = [
#     path(r'users/<int:pk>/', Users.as_view()),
#     path(r'users/', Users.as_view()),
# ]
