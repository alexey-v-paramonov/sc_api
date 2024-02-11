from rest_framework import permissions


class UserOwnsApp(permissions.BasePermission):

    def has_permission(self, request, view):
        app_id = view.kwargs.get("app_id")

        if app_id is None:
            return False

        app = view.app_model.objects.get(pk=app_id)
        return app.user_id == request.user.id