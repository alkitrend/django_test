from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        RIDER = 'rider', 'Rider'
        DRIVER = 'driver', 'Driver'
        OTHER = 'other', 'Other'

    id_user = models.BigAutoField(primary_key=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.OTHER)
    phone_number = models.CharField(max_length=32, blank=True)
    email = models.EmailField(unique=True)

    def __str__(self) -> str:
        return f'{self.username} ({self.role})'
