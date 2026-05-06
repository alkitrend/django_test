from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import viewsets

from .models import Ride, RideEvent
from .permissions import IsAdminRole
from .serializers import RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    permission_classes = (IsAdminRole,)
    filterset_fields = ('status', 'id_rider__email')
    ordering_fields = ('pickup_time',)
    ordering = ('-pickup_time',)

    def get_queryset(self):
        recent_threshold = timezone.now() - timedelta(hours=24)
        recent_events = RideEvent.objects.filter(created_at__gte=recent_threshold).order_by('-created_at')
        return (
            Ride.objects.select_related('id_rider', 'id_driver')
            .prefetch_related(
                Prefetch(
                    'ride_events',
                    queryset=recent_events,
                    to_attr='todays_ride_events_prefetched',
                )
            )
            .all()
        )
