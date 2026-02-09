from django.db import models
from django.contrib.auth.models import AbstractUser
from users.managers import UserManager
import uuid

class Language:

    ENG = 0
    RU = 1

    choices = (
        (ENG, 'English'),
        (RU, 'Russian'),
    )

class Currency:

    USD = 0
    RUB = 1
    EUR = 2

    choices = (
        (USD, '$'),
        (RUB, '₽'),
        (EUR, '€'),
    )



class User(AbstractUser):
    username = None
    email = models.EmailField("Email address", unique=True)
    language = models.PositiveSmallIntegerField(
        "Language",
        default=Language.ENG,
        choices=Language.choices,
    )
    currency = models.PositiveSmallIntegerField(
        "Currency",
        default=Currency.USD,
        choices=Currency.choices,
    )
    balance = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    agreement_accepted = models.BooleanField(
        default=False,
    )
    subscribed = models.BooleanField(
        default=True,
    )
    stale_notification_sent_ts = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When a stale-user notification was sent to this user.",
    )
    email_confirmed = models.BooleanField(
        default=False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def is_english(self):
        return self.language == Language.ENG

    def is_russian(self):
        return self.language == Language.RU
    
    
    def is_usd(self):
        return self.currency == Currency.USD

    def is_rub(self):
        return self.currency == Currency.RUB


class EmailConfirmationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_confirmation_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"EmailConfirmationToken for {self.user.email}"