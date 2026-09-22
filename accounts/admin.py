from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone_num', 'username', 'is_verified', 'is_staff']
    list_filter = ['is_verified', 'is_staff']
    search_fields = ['phone_num', 'username']
    fieldsets = UserAdmin.fieldsets + (
        ('OTP Info', {'fields': ('phone_num', 'otp', 'is_verified')}),
    )
