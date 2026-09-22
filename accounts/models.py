from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone_num = models.CharField(max_length=20, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_num'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.phone_num
