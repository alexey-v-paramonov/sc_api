from django.db.models.signals import post_save
from django.dispatch import receiver
from radio.models import SelfHostedRadio, HostedRadio
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings


@receiver(post_save, sender=HostedRadio)
def send_email_notification(sender, instance, created, **kwargs):
    if created:
        template = get_template('email/hosted_created.html')
        content = template.render({'radio': instance})
        msg = EmailMessage("New hosted radio", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
        msg.send()

@receiver(post_save, sender=SelfHostedRadio)
def send_email_notification(sender, instance, created, **kwargs):
    if created:
        template = get_template('email/self_hosted_created.html')
        content = template.render({'radio': instance})
        msg = EmailMessage("New self-hosted radio", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
        msg.send()
