from django.contrib import admin

from radio.models import RadioServer, SelfHostedRadio, HostedRadio

admin.site.register(RadioServer)
admin.site.register(SelfHostedRadio)
admin.site.register(HostedRadio)