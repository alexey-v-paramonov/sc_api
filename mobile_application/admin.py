from django.contrib import admin

from mobile_application.models import AndroidApplication, IosApplication, AndroidApplicationRadio, IosApplicationRadio, AndroidApplicationRadioChannel, IosApplicationRadioChannel

admin.site.register(AndroidApplication)
admin.site.register(IosApplication)
admin.site.register(AndroidApplicationRadio)
admin.site.register(IosApplicationRadio)
admin.site.register(AndroidApplicationRadioChannel)
admin.site.register(IosApplicationRadioChannel)