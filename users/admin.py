from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect
from rest_framework.authtoken.models import Token

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
        "account_actions", 
    )

    ordering = ('-date_joined',)
    exclude = ('username',)
    fieldsets = (
        (None, {'fields': ( 'email', 'password',  'balance', 'currency', 'language')}),
    )
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [path("<int:user_id>/loginas/", self.admin_site.admin_view(self.loginas))]
        return custom_urls + urls    

    def loginas(self, request, user_id, *args, **kwargs):
        user = User.objects.get(pk=user_id)
        token, _ = Token.objects.get_or_create(user=user)
        domain = "streaming.center"
        if user.is_russian():
            domain = "radio-tochka.com"
        return HttpResponseRedirect(f"https://app.{domain}/login/?t={token.key}&id={user.id}&email={user.email}")

    def account_actions(self, obj):
        return format_html(f"<a class=\"button\" href=\"/admin/users/user/{obj.id}/loginas\">Login as</a>&nbsp;")
    account_actions.short_description = 'Account Actions'
    account_actions.allow_tags = True


admin.site.register(User, UserAdmin)