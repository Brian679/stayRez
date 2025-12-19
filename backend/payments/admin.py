from django.contrib import admin
from .models import AdminFeePayment, PaymentConfirmation, ContactView


@admin.register(PaymentConfirmation)
class PaymentConfirmationAdmin(admin.ModelAdmin):
    list_display = ("payment", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("payment__user__email", "payment__university__name")


@admin.register(AdminFeePayment)
class AdminFeePaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "university", "amount", "uses_remaining", "valid_until")
    search_fields = ("user__email", "university__name")


@admin.register(ContactView)
class ContactViewAdmin(admin.ModelAdmin):
    list_display = ("payment", "property", "viewed_at")
    list_filter = ("viewed_at",)
    search_fields = ("payment__user__email", "property__title")
    readonly_fields = ("viewed_at",)
