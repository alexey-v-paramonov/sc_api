
from django.urls import path

from users.views import users_router, PasswordResetView, PasswordResetConfirmView, EmailConfirmationView
#UsersView

urlpatterns = users_router.urls

urlpatterns += path(r'password_reset/', PasswordResetView.as_view()),
urlpatterns += path(r'password_reset/confirm/', PasswordResetConfirmView.as_view()),

# urlpatterns = [
#     path(r'users/<int:pk>/', Users.as_view()),
#     path(r'users/', Users.as_view()),
# ]
