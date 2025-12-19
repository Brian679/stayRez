from rest_framework import serializers
from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    admin_fee = serializers.SerializerMethodField()
    booking_history = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "full_name",
            "phone_number",
            "address",
            "role",
            "admin_fee",
            "booking_history",
        )
        read_only_fields = ("email", "role", "admin_fee", "booking_history")

    def get_admin_fee(self, user):
        """Return current admin-fee entitlement and remaining accommodation views.

        This is the number of accommodations the user can still unlock contact details for.
        """
        try:
            from django.utils import timezone
            from payments.models import AdminFeePayment

            now = timezone.now()
            payment = (
                AdminFeePayment.objects.filter(user=user, uses_remaining__gt=0)
                .exclude(valid_until__lt=now)
                .select_related("university")
                .order_by("-created_at")
                .first()
            )
            if not payment:
                return {
                    "is_active": False,
                    "uses_remaining": 0,
                    "valid_until": None,
                    "university": None,
                    "amount": None,
                }
            return {
                "is_active": True,
                "uses_remaining": int(payment.uses_remaining or 0),
                "valid_until": payment.valid_until,
                "university": getattr(payment.university, "name", None),
                "amount": payment.amount,
            }
        except Exception:
            return {
                "is_active": False,
                "uses_remaining": 0,
                "valid_until": None,
                "university": None,
                "amount": None,
            }

    def get_booking_history(self, user):
        """Best-effort booking/history.

        There is no dedicated Booking model in the current backend.
        We use ContactView entries (when user unlocks landlord contact details) as history.
        """
        try:
            from payments.models import ContactView

            qs = (
                ContactView.objects.filter(payment__user=user)
                .select_related("property", "payment", "payment__university")
                .order_by("-viewed_at")[:20]
            )
            out = []
            for cv in qs:
                out.append(
                    {
                        "viewed_at": cv.viewed_at,
                        "property_id": getattr(cv.property, "id", None),
                        "property_title": getattr(cv.property, "title", ""),
                        "university": getattr(getattr(cv.payment, "university", None), "name", None),
                    }
                )
            return out
        except Exception:
            return []


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "username", "full_name", "phone_number", "address", "role")

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            username=validated_data.get("username"),
            full_name=validated_data.get("full_name", ""),
            phone_number=validated_data.get("phone_number", ""),
            address=validated_data.get("address", ""),
            role=validated_data.get("role", "general"),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "username", "full_name", "phone_number", "address", "role")
        read_only_fields = ("email", "role")
