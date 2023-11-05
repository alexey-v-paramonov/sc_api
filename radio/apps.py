from __future__ import unicode_literals

from django.apps import AppConfig


class RadioConfig(AppConfig):
    name = 'radio'

    def ready(self):
        import radio.signals
