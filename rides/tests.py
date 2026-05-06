from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Ride, RideEvent, User


class RideApiTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@example.com',
            password='secret123',
            role=User.Role.ADMIN,
        )
        self.non_admin_user = User.objects.create_user(
            username='rider1',
            email='rider@example.com',
            password='secret123',
            role=User.Role.RIDER,
        )
        self.driver_user = User.objects.create_user(
            username='driver1',
            email='driver@example.com',
            password='secret123',
            role=User.Role.DRIVER,
        )
        self.other_rider = User.objects.create_user(
            username='rider2',
            email='rider2@example.com',
            password='secret123',
            role=User.Role.RIDER,
        )

        now = timezone.now()
        self.ride_a = Ride.objects.create(
            status=Ride.Status.PICKUP,
            id_rider=self.non_admin_user,
            id_driver=self.driver_user,
            pickup_latitude=37.7749,
            pickup_longitude=-122.4194,
            dropoff_latitude=37.7849,
            dropoff_longitude=-122.4094,
            pickup_time=now - timedelta(hours=3),
        )
        self.ride_b = Ride.objects.create(
            status=Ride.Status.DROPOFF,
            id_rider=self.other_rider,
            id_driver=self.driver_user,
            pickup_latitude=34.0522,
            pickup_longitude=-118.2437,
            dropoff_latitude=34.0622,
            dropoff_longitude=-118.2337,
            pickup_time=now - timedelta(hours=1),
        )

        RideEvent.objects.create(
            id_ride=self.ride_a,
            description='Status changed to pickup',
            created_at=now - timedelta(hours=2),
        )
        RideEvent.objects.create(
            id_ride=self.ride_a,
            description='Older event that should be excluded',
            created_at=now - timedelta(days=2),
        )

    def _list_url(self):
        return reverse('ride-list')

    def test_non_admin_cannot_access_ride_api(self):
        self.client.force_authenticate(user=self.non_admin_user)
        response = self.client.get(self._list_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_and_get_paginated_results(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_todays_ride_events_only_contains_last_24_hours(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._list_url(), {'status': Ride.Status.PICKUP})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        events = response.data['results'][0]['todays_ride_events']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['description'], 'Status changed to pickup')

    def test_filter_by_rider_email(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._list_url(), {'rider_email': 'rider2@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id_rider']['email'], 'rider2@example.com')

    def test_order_by_pickup_time(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._list_url(), {'ordering': 'pickup_time'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id_ride'] for item in response.data['results']]
        self.assertEqual(ids, [self.ride_a.id_ride, self.ride_b.id_ride])

    def test_distance_ordering_requires_lat_lng(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self._list_url(), {'ordering': 'distance_to_pickup'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_order_by_distance_to_pickup(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            self._list_url(),
            {'ordering': 'distance_to_pickup', 'lat': 37.7749, 'lng': -122.4194},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id_ride'] for item in response.data['results']]
        self.assertEqual(ids[0], self.ride_a.id_ride)
