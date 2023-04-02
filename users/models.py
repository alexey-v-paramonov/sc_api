from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    username = None
    email = models.EmailField("Email address", unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []