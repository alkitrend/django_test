from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Wingz Fields', {'fields': ('id_user', 'role', 'phone_number')}),
    )
    readonly_fields = ('id_user',)
