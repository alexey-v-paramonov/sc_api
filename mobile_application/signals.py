from django.db.models.signals import post_save
from django.dispatch import receiver
from mobile_application.models import AndroidApplication, IosApplication
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings


@receiver(post_save, sender=AndroidApplication)
def send_email_notification(sender, instance, created, **kwargs):
    if created:
        template = get_template('email/android_app_created.html')
        content = template.render({'app': instance})
        msg = EmailMessage("New Android app", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
        msg.send()

@receiver(post_save, sender=IosApplication)
def send_email_notification(sender, instance, created, **kwargs):
    if created:
        template = get_template('email/ios_app_created.html')
        content = template.render({'app': instance})
        msg = EmailMessage("New iOs app", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
        msg.send()
