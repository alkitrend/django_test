from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Ride, RideEvent, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Wingz Fields', {'fields': ('id_user', 'role', 'phone_number')}),
    )
    readonly_fields = ('id_user',)


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id_ride', 'status', 'id_rider', 'id_driver', 'pickup_time')
    search_fields = ('id_ride', 'id_rider__email', 'id_driver__email')
    list_filter = ('status',)
    list_select_related = ('id_rider', 'id_driver')


@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ('id_ride_event', 'id_ride', 'description', 'created_at')
    search_fields = ('description', 'id_ride__id_ride')
    list_filter = ('created_at',)
    list_select_related = ('id_ride',)
