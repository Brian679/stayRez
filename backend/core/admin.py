from django.contrib import admin
from .models import Notification, UserUniversityPreference, ContactMessage
from .models_feedback import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "easy_to_use", "user_friendly", "submitted_at")
    search_fields = ("name", "like_most", "improvements")
    list_filter = ("age", "gender", "occupation", "city")


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
