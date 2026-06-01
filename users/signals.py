from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage

from django.conf import settings
from django.template.loader import get_template


@receiver(post_save, sender="users.User")
def user_post_save(sender, instance, created, **kwargs):
    pass

