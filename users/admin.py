from django.contrib import admin

from users.models import User


class UserAdmin(admin.ModelAdmin):
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

admin.site.register(User, UserAdmin)