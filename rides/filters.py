import django_filters

from .models import Ride


class RideFilterSet(django_filters.FilterSet):
    rider_email = django_filters.CharFilter(field_name='id_rider__email', lookup_expr='iexact')

    class Meta:
        model = Ride
        fields = ('status', 'rider_email')
