from django.db import models
from django.conf import settings

# Create your models here.
class InvoiceRequest(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Owner",
        blank=False,
        null=False,
        on_delete=models.deletion.CASCADE
    )

    email = models.EmailField("Email address")
    amount = models.PositiveIntegerField(
        null=False,
        blank=False,
    )
    is_paid = models.BooleanField(
        default=False,
    )


