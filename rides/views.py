from datetime import timedelta

from django.db.models import ExpressionWrapper, F, FloatField, Prefetch, Value
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets

from .filters import RideFilterSet
from .models import Ride, RideEvent
from .permissions import IsAdminRole
from .serializers import RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    permission_classes = (IsAdminRole,)
    filterset_class = RideFilterSet
    ordering_fields = ('pickup_time', 'distance_to_pickup')
    ordering = ('-pickup_time',)

    def get_queryset(self):
        recent_threshold = timezone.now() - timedelta(hours=24)
        recent_events = RideEvent.objects.filter(created_at__gte=recent_threshold).order_by('-created_at')
        queryset = (
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
        return self._annotate_distance_if_requested(queryset)

    def _annotate_distance_if_requested(self, queryset):
        ordering_param = self.request.query_params.get('ordering', '')
        if 'distance_to_pickup' not in ordering_param:
            return queryset

        lat_raw = self.request.query_params.get('lat')
        lng_raw = self.request.query_params.get('lng')
        if lat_raw is None or lng_raw is None:
            raise ValidationError({'detail': 'Query params lat and lng are required when ordering by distance_to_pickup.'})

        try:
            lat = float(lat_raw)
            lng = float(lng_raw)
        except ValueError as exc:
            raise ValidationError({'detail': 'lat and lng must be valid floating point values.'}) from exc

        distance_expr = ExpressionWrapper(
            (F('pickup_latitude') - Value(lat)) * (F('pickup_latitude') - Value(lat))
            + (F('pickup_longitude') - Value(lng)) * (F('pickup_longitude') - Value(lng)),
            output_field=FloatField(),
        )
        return queryset.annotate(distance_to_pickup=distance_expr)
