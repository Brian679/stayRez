from django.contrib import admin
from .models import Notification, UserUniversityPreference, ContactMessage


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("recipient__email", "title")


@admin.register(UserUniversityPreference)
class UserUniversityPreferenceAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "user", "university", "visit_count", "last_visited")
    list_filter = ("university",)
    search_fields = ("ip_address", "user__email", "university__name")
    readonly_fields = ("created_at", "last_visited")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("username", "phone_number", "created_at")
    search_fields = ("username", "phone_number", "message")
    readonly_fields = ("created_at", "ip_address", "user")
