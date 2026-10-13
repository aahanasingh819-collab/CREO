from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CreoUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('CREO', {'fields': ('role',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('CREO', {'fields': ('email', 'role')}),)
    list_display = ['username', 'email', 'role', 'is_staff']
