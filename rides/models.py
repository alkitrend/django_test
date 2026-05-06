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


class Ride(models.Model):
    class Status(models.TextChoices):
        EN_ROUTE = 'en-route', 'En Route'
        PICKUP = 'pickup', 'Pickup'
        DROPOFF = 'dropoff', 'Dropoff'

    id_ride = models.BigAutoField(primary_key=True)
    status = models.CharField(max_length=32, choices=Status.choices, db_index=True)
    id_rider = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='rides_as_rider',
        db_column='id_rider',
    )
    id_driver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='rides_as_driver',
        db_column='id_driver',
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ('-pickup_time',)
        indexes = [
            models.Index(fields=['status', 'pickup_time']),
            models.Index(fields=['id_rider', 'pickup_time']),
            models.Index(fields=['id_driver', 'pickup_time']),
        ]

    def __str__(self) -> str:
        return f'Ride {self.id_ride} ({self.status})'


class RideEvent(models.Model):
    id_ride_event = models.BigAutoField(primary_key=True)
    id_ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name='ride_events',
        db_column='id_ride',
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['id_ride', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'RideEvent {self.id_ride_event} for Ride {self.id_ride_id}'
