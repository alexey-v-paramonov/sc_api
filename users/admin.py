from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


class UserAdmin(UserAdmin):
    model = User
    list_per_page = 1500
    search_fields = ['email', ]
    list_display = (
        "id",
        "date_joined",
        "email",
        "balance",
        "currency",
        "language",
    )
    ordering = ('-date_joined',)


admin.site.register(User, UserAdmin)