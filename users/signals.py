from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage, EmailMultiAlternatives

from django.conf import settings
from django.template.loader import get_template

from users.models import User


@receiver(post_save, sender="users.User")
def user_post_save(sender, instance, created, **kwargs):
    if not created:
        return


    # Send email to admin
    template = get_template('email/user_created.html')
    content = template.render({'user': instance})
    msg = EmailMessage("New User", content, settings.ADMIN_EMAIL, to=[settings.ADMIN_EMAIL,])
    msg.send()

