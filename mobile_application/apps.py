from django.apps import AppConfig


class MobileApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mobile_application'

    def ready(self):
        import mobile_application.signals
