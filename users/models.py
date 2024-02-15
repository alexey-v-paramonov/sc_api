from django.db import models
from django.contrib.auth.models import AbstractUser
from users.managers import UserManager

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

    choices = (
        (USD, '$'),
        (RUB, '₽'),
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
    balance = models.FloatField(null=False, blank=False, default=0)
    agreement_accepted = models.BooleanField(
        default=False,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def is_english(self):
        return self.language == Language.ENG

    def is_russian(self):
        return self.language == Language.RU