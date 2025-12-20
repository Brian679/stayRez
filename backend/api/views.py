from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
try:
    from rest_framework_simplejwt.views import TokenObtainPairView as _TokenObtainPairView

    class TokenObtainPairView(_TokenObtainPairView):
        pass
except Exception:
    # SimpleJWT not installed; provide a fallback 501 endpoint
    from rest_framework import status

    class TokenObtainPairView(APIView):
        def post(self, request, *args, **kwargs):
            return Response({"detail": "SimpleJWT not installed. Install djangorestframework-simplejwt to enable token auth."}, status=status.HTTP_501_NOT_IMPLEMENTED)

from accounts.serializers import RegisterSerializer, UserSerializer, UserProfileSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Allow an authenticated user to change password.

    Body:
    - old_password
    - new_password
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'detail': 'old_password and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        # Keep the current session alive for session-auth clients
        try:
            from django.contrib.auth import update_session_auth_hash

            update_session_auth_hash(request, user)
        except Exception:
            pass

        return Response({'detail': 'Password updated'}, status=status.HTTP_200_OK)
from properties.models import University, Property, Service, City
from payments.models import PaymentConfirmation, AdminFeePayment
from .serializers import UniversitySerializer, PropertySerializer, PaymentConfirmationSerializer, ReviewSerializer, PropertyDetailSerializer, ServiceSerializer


class CityListView(APIView):
    """List cities for mobile + web parity.

    Query params:
    - property_type: single type (e.g. long_term)
    - property_types: comma-separated types (e.g. resort,real_estate,shop)
    - include_empty: 1/0 (default 1) include cities with 0 listings
    - include_breakdown: 1/0 include resorts/lodges/shops counts
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        from django.db.models import Count, Q, Min, Max

        include_empty = request.query_params.get("include_empty", "1").lower() in ("1", "true", "yes")
        include_breakdown = request.query_params.get("include_breakdown", "0").lower() in ("1", "true", "yes")

        property_type = request.query_params.get("property_type")
        property_types_param = request.query_params.get("property_types")

        types = []
        if property_types_param:
            types = [t.strip() for t in property_types_param.split(",") if t.strip()]
        elif property_type:
            types = [property_type]

        # Choose price field based on type set.
        if types and all(t in ("long_term", "shop") for t in types):
            price_field = "price_per_month"
        else:
            price_field = "nightly_price"

        prop_filter = Q(property__is_approved=True, property__is_available=True)
        if types:
            prop_filter &= Q(property__property_type__in=types)

        qs = (
            City.objects.all()
            .order_by("name")
            .annotate(
                properties_count=Count("property", filter=prop_filter, distinct=True),
                min_price=Min(f"property__{price_field}", filter=prop_filter),
                max_price=Max(f"property__{price_field}", filter=prop_filter),
            )
        )

        if include_breakdown:
            qs = qs.annotate(
                resorts_count=Count(
                    "property",
                    filter=Q(property__is_approved=True, property__is_available=True, property__property_type="resort"),
                    distinct=True,
                ),
                lodges_count=Count(
                    "property",
                    filter=Q(property__is_approved=True, property__is_available=True, property__property_type="real_estate"),
                    distinct=True,
                ),
                shops_count=Count(
                    "property",
                    filter=Q(property__is_approved=True, property__is_available=True, property__property_type="shop"),
                    distinct=True,
                ),
            )

        if not include_empty:
            qs = qs.filter(properties_count__gt=0)

        # Provide a representative image per city if possible (best-effort).
        # This is intentionally small/naive since dev DB sizes are small.
        out = []
        for city in qs:
            sample_thumbnail = None
            try:
                prop_qs = Property.objects.filter(is_approved=True, is_available=True, city=city)
                if types:
                    prop_qs = prop_qs.filter(property_type__in=types)
                prop = prop_qs.prefetch_related("images").order_by("-created_at").first()
                if prop:
                    img = prop.images.first()
                    if img:
                        url = img.image.url
                        sample_thumbnail = request.build_absolute_uri(url)
            except Exception:
                sample_thumbnail = None

            payload = {
                "id": city.id,
                "name": city.name,
                "properties_count": getattr(city, "properties_count", 0) or 0,
                "min_price": getattr(city, "min_price", None),
                "max_price": getattr(city, "max_price", None),
                "sample_thumbnail": sample_thumbnail,
            }
            if include_breakdown:
                payload.update(
                    {
                        "resorts_count": getattr(city, "resorts_count", 0) or 0,
                        "lodges_count": getattr(city, "lodges_count", 0) or 0,
                        "shops_count": getattr(city, "shops_count", 0) or 0,
                    }
                )
            out.append(payload)

        return Response(out)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


# Session-based login/logout for clients that prefer cookies (mobile can use this too)
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate, login, logout

class LoginView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"detail": "logged out"}, status=status.HTTP_200_OK)

# Token refresh/verify views (wrap SimpleJWT if installed, else return 501)
try:
    from rest_framework_simplejwt.views import TokenRefreshView as _TokenRefreshView, TokenVerifyView as _TokenVerifyView

    class TokenRefreshView(_TokenRefreshView):
        pass

    class TokenVerifyView(_TokenVerifyView):
        pass
except Exception:
    class TokenRefreshView(APIView):
        def post(self, request, *args, **kwargs):
            return Response({"detail": "SimpleJWT not installed. Install djangorestframework-simplejwt to enable token refresh."}, status=status.HTTP_501_NOT_IMPLEMENTED)

    class TokenVerifyView(APIView):
        def post(self, request, *args, **kwargs):
            return Response({"detail": "SimpleJWT not installed. Install djangorestframework-simplejwt to enable token verify."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class UniversityListView(generics.ListAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.AllowAny]


class ServiceListView(generics.ListAPIView):
    """List all active services for home screen"""
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]


class UniversityDetailView(generics.RetrieveAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [permissions.AllowAny]


class UniversityPropertiesView(generics.ListAPIView):
    serializer_class = PropertySerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        uni_id = self.kwargs.get("pk")
        qs = Property.objects.filter(is_approved=True, is_available=True, university_id=uni_id)
        qs = self.apply_filters(qs)
        # distance-based ordering if lat/lng provided
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius_km")
        order = request.query_params.get("order")
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                radius_val = float(radius) if radius else None
                results = []
                from math import radians, sin, cos, atan2, sqrt
                R = 6371
                for p in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
                    try:
                        phi1 = radians(lat)
                        phi2 = radians(float(p.latitude))
                        dphi = radians(float(p.latitude) - lat)
                        dlambda = radians(float(p.longitude) - lng)
                        a = sin(dphi/2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda/2) ** 2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance = R * c
                        p.distance_km = round(distance, 2)
                        if radius_val is None or distance <= radius_val:
                            results.append(p)
                    except Exception:
                        continue
                # ordering
                if order == "distance_desc":
                    results.sort(key=lambda x: getattr(x, "distance_km", 9999), reverse=True)
                else:
                    # default distance_asc
                    results.sort(key=lambda x: getattr(x, "distance_km", 9999))
                page = self.paginate_queryset(results)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                serializer = self.get_serializer(results, many=True)
                return Response({"results": serializer.data})
            except ValueError:
                pass
        # no lat/lng: use queryset ordering
        if order in ("price_asc", "price_desc"):
            qs = qs.order_by("nightly_price" if order == "price_asc" else "-nightly_price")
        elif order == "newest":
            qs = qs.order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({"results": serializer.data})

    def apply_filters(self, qs):
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
        gender = self.request.query_params.get("gender")
        if gender:
            qs = qs.filter(gender=gender)
        sharing = self.request.query_params.get("sharing")
        if sharing:
            qs = qs.filter(sharing=sharing)
        overnight = self.request.query_params.get("overnight")
        if overnight is not None:
            if overnight.lower() in ("1", "true", "yes"):
                qs = qs.filter(overnight=True)
            elif overnight.lower() in ("0", "false", "no"):
                qs = qs.filter(overnight=False)
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        # Choose price field based on property type (if provided).
        property_type = self.request.query_params.get("property_type")
        property_types_param = self.request.query_params.get("property_types")
        types = []
        if property_types_param:
            types = [t.strip() for t in property_types_param.split(",") if t.strip()]
        elif property_type:
            types = [property_type]
        if types:
            qs = qs.filter(property_type__in=types)

        price_field = "price_per_month" if (types and all(t in ("long_term", "shop") for t in types)) else "nightly_price"
        try:
            if min_price:
                qs = qs.filter(**{f"{price_field}__gte": float(min_price)})
            if max_price:
                qs = qs.filter(**{f"{price_field}__lte": float(max_price)})
        except ValueError:
            pass
        return qs


class PropertyListView(generics.ListAPIView):
    serializer_class = PropertySerializer
    permission_classes = [permissions.AllowAny]

    def apply_filters(self, qs):
        # reuse same filtering logic as university view
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
        gender = self.request.query_params.get("gender")
        if gender:
            qs = qs.filter(gender=gender)
        sharing = self.request.query_params.get("sharing")
        if sharing:
            qs = qs.filter(sharing=sharing)
        overnight = self.request.query_params.get("overnight")
        if overnight is not None:
            if overnight.lower() in ("1", "true", "yes"):
                qs = qs.filter(overnight=True)
            elif overnight.lower() in ("0", "false", "no"):
                qs = qs.filter(overnight=False)
        property_type = self.request.query_params.get("property_type")
        property_types_param = self.request.query_params.get("property_types")
        types = []
        if property_types_param:
            types = [t.strip() for t in property_types_param.split(",") if t.strip()]
        elif property_type:
            types = [property_type]
        if types:
            qs = qs.filter(property_type__in=types)

        # City filtering
        city_id = self.request.query_params.get("city_id") or self.request.query_params.get("city")
        city_name = self.request.query_params.get("city_name")
        if city_id:
            try:
                qs = qs.filter(city_id=int(city_id))
            except ValueError:
                pass
        elif city_name:
            qs = qs.filter(city__name__iexact=city_name)

        # Price filtering
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        price_field = "price_per_month" if (types and all(t in ("long_term", "shop") for t in types)) else "nightly_price"
        try:
            if min_price:
                qs = qs.filter(**{f"{price_field}__gte": float(min_price)})
            if max_price:
                qs = qs.filter(**{f"{price_field}__lte": float(max_price)})
        except ValueError:
            pass
        return qs

    def get(self, request, *args, **kwargs):
        qs = Property.objects.filter(is_approved=True, is_available=True)
        qs = self.apply_filters(qs)
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius_km")
        order = request.query_params.get("order")
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                radius_val = float(radius) if radius else None
                results = []
                from math import radians, sin, cos, atan2, sqrt
                R = 6371
                for p in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
                    try:
                        phi1 = radians(lat)
                        phi2 = radians(float(p.latitude))
                        dphi = radians(float(p.latitude) - lat)
                        dlambda = radians(float(p.longitude) - lng)
                        a = sin(dphi/2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda/2) ** 2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance = R * c
                        p.distance_km = round(distance, 2)
                        if radius_val is None or distance <= radius_val:
                            results.append(p)
                    except Exception:
                        continue
                if order == "distance_desc":
                    results.sort(key=lambda x: getattr(x, "distance_km", 9999), reverse=True)
                else:
                    results.sort(key=lambda x: getattr(x, "distance_km", 9999))
                page = self.paginate_queryset(results)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                serializer = self.get_serializer(results, many=True)
                return Response({"results": serializer.data})
            except ValueError:
                pass
        # Price ordering: use monthly for long-term/shop, otherwise nightly.
        property_type = request.query_params.get("property_type")
        property_types_param = request.query_params.get("property_types")
        types = []
        if property_types_param:
            types = [t.strip() for t in property_types_param.split(",") if t.strip()]
        elif property_type:
            types = [property_type]

        price_field = "price_per_month" if (types and all(t in ("long_term", "shop") for t in types)) else "nightly_price"

        if order in ("price_asc", "price_desc"):
            qs = qs.order_by(price_field if order == "price_asc" else f"-{price_field}")
        elif order == "newest":
            qs = qs.order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({"results": serializer.data})

class PropertyDetailView(generics.RetrieveAPIView):
    queryset = Property.objects.filter(is_approved=True, is_available=True)
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.AllowAny]


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        prop_id = self.kwargs.get("pk")
        prop = Property.objects.get(pk=prop_id)
        if prop.reviews.filter(user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "You have already submitted a review for this property."})
        serializer.save(user=self.request.user, property=prop)


# Landlord property upload
from .permissions import IsLandlordRole
from .serializers_property import PropertyCreateSerializer, PropertyImageSerializer


class LandlordPropertyCreateView(generics.CreateAPIView):
    serializer_class = PropertyCreateSerializer
    permission_classes = [IsLandlordRole]

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class LandlordPropertyListView(generics.ListAPIView):
    serializer_class = PropertySerializer
    permission_classes = [IsLandlordRole]

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)


class LandlordPropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PropertyCreateSerializer
    permission_classes = [IsLandlordRole]

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        was_approved = bool(getattr(serializer.instance, "is_approved", False))
        prop = serializer.save()
        # Once approved, landlord edits should not require re-approval.
        if not was_approved and prop.is_approved:
            prop.is_approved = False
            prop.save(update_fields=['is_approved'])


class LandlordActivityListView(generics.ListAPIView):
    """Activity feed for landlords.

    Mirrors the web dashboard section which shows when users unlocked contact
    details for the landlord's listings (ContactView entries).
    """

    permission_classes = [IsLandlordRole]

    def list(self, request, *args, **kwargs):
        from payments.models import ContactView

        qs = (
            ContactView.objects.filter(property__owner=request.user)
            .select_related('payment__user', 'property')
            .order_by('-viewed_at')[:50]
        )
        out = []
        for cv in qs:
            out.append(
                {
                    'viewed_at': cv.viewed_at,
                    'property_id': getattr(cv.property, 'id', None),
                    'property_title': getattr(cv.property, 'title', ''),
                    'viewer_email': getattr(getattr(cv.payment, 'user', None), 'email', ''),
                }
            )
        return Response(out)


# Nearby map-search endpoint
from django.db.models import F, FloatField, ExpressionWrapper
import math


def haversine_expression(lat_field, lng_field, lat, lng):
    # Use approximate formula via DB-side Arithmetic when possible, otherwise filter in Python
    # This expresses distance in kilometers using Haversine formula approximation
    # For SQLite (dev) we will fallback to Python filtering in view.
    return None


class NearbyPropertiesView(generics.ListAPIView):
    serializer_class = PropertySerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = float(request.query_params.get("radius_km", 5))
        qs = Property.objects.filter(is_approved=True, is_available=True)
        if lat and lng:
            try:
                lat = float(lat)
                lng = float(lng)
                # filter in Python after narrowing to ones with lat/lng
                qs = qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
                results = []
                for p in qs:
                    try:
                        from math import radians, sin, cos, atan2, sqrt
                        R = 6371
                        phi1 = radians(lat)
                        phi2 = radians(float(p.latitude))
                        dphi = radians(float(p.latitude) - lat)
                        dlambda = radians(float(p.longitude) - lng)
                        a = sin(dphi/2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda/2) ** 2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance = R * c
                        if distance <= radius:
                            p.distance_km = round(distance, 2)
                            results.append(p)
                    except Exception:
                        continue
                # sort by distance
                results.sort(key=lambda x: getattr(x, "distance_km", 9999))
                page = self.paginate_queryset(results)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                # no paginator configured - return results in a compatible format
                serializer = self.get_serializer(results, many=True)
                return Response({"results": serializer.data})
            except ValueError:
                pass
        # fallback: return list without distance
        return super().get(request, *args, **kwargs)


class PaymentConfirmationCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # create serializer handles admin fee calculation and payment creation
        if self.request.method == "POST":
            from .serializers import CreatePaymentConfirmationSerializer

            return CreatePaymentConfirmationSerializer
        return PaymentConfirmationSerializer

    def perform_create(self, serializer):
        confirmation = serializer.save()
        # Post-save signals will create notifications for admins
        return confirmation


class NotifyAdminPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        """Notify admin to check pending payment"""
        from django.contrib.auth import get_user_model
        
        try:
            payment = AdminFeePayment.objects.get(pk=pk, user=request.user)
            confirmation = payment.confirmations.filter(status='pending').first()
            
            if not confirmation:
                return Response({"detail": "No pending payment confirmation found."}, status=400)
            
            # Notify all admin users
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    title="Payment Check Requested",
                    message=f"{request.user.email} is requesting review of their payment for {payment.university.name}. Amount: ${payment.amount}."
                )
            
            return Response({"detail": "Admin has been notified."})
        except AdminFeePayment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=404)


class CancelPaymentConfirmationView(APIView):
    """Allow a user to cancel their own pending payment confirmation.

    Soft-cancel only: the record remains in DB and status becomes 'canceled'.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            confirmation = PaymentConfirmation.objects.select_related("payment").get(pk=pk)
        except PaymentConfirmation.DoesNotExist:
            return Response({"detail": "Payment confirmation not found."}, status=404)

        if confirmation.payment.user_id != request.user.id:
            # Don't leak existence across users
            return Response({"detail": "Payment confirmation not found."}, status=404)

        if confirmation.status != "pending":
            return Response({"detail": "Only pending confirmations can be canceled."}, status=400)

        confirmation.status = "canceled"
        confirmation.save(update_fields=["status"])
        return Response({"status": "canceled"}, status=200)


# Admin actions for payment confirmations
from .permissions import IsAdminRole
from payments.models import AdminFeePayment, PaymentConfirmation
from core.models import Notification
from properties.models import Property
from .serializers import PropertyContactSerializer


class ApprovePaymentConfirmationView(generics.UpdateAPIView):
    permission_classes = [IsAdminRole]
    queryset = PaymentConfirmation.objects.all()
    serializer_class = PaymentConfirmationSerializer

    def update(self, request, *args, **kwargs):
        confirmation = self.get_object()
        confirmation.status = "approved"
        confirmation.save()
        # activate the related AdminFeePayment
        payment = confirmation.payment
        payment.activate()
        # notify the user
        Notification.objects.create(
            recipient=payment.user,
            title="Payment confirmed",
            message=f"Your payment for {payment.university.name} has been approved. You can now view landlord contacts for up to {payment.allowed_accommodations} accommodations.",
        )
        return Response({"status": "approved"})


class DeclinePaymentConfirmationView(generics.UpdateAPIView):
    permission_classes = [IsAdminRole]
    queryset = PaymentConfirmation.objects.all()
    serializer_class = PaymentConfirmationSerializer

    def update(self, request, *args, **kwargs):
        confirmation = self.get_object()
        confirmation.status = "declined"
        confirmation.save()
        payment = confirmation.payment
        Notification.objects.create(
            recipient=payment.user,
            title="Payment declined",
            message=f"Your payment confirmation for {payment.university.name} was declined by admin.",
        )
        return Response({"status": "declined"})


class ApprovePropertyView(generics.UpdateAPIView):
    permission_classes = [IsAdminRole]
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def update(self, request, *args, **kwargs):
        prop = self.get_object()
        prop.is_approved = True
        prop.save()
        # notify owner
        Notification.objects.create(
            recipient=prop.owner,
            title="Property approved",
            message=f"Your property '{prop.title}' has been approved and is now visible to users.",
        )
        return Response({"status": "approved"})


class ContactLandlordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyContactSerializer

    def post(self, request, pk):
        """If user has active AdminFeePayment for this university with uses_remaining>0, return contact details and decrement uses_remaining by 1.
        Otherwise return payment instructions and calculated total when user provides 'students' in payload."""
        prop = generics.get_object_or_404(Property, pk=pk)
        user = request.user
        # check for active payments for this university
        active_payments = AdminFeePayment.objects.filter(user=user, university=prop.university)
        active = None
        for p in active_payments:
            if p.is_active():
                active = p
                break

        if active:
            # decrement uses and return contact
            if active.uses_remaining <= 0:
                return Response({"detail": "No remaining uses on your approved payment. Please pay again."}, status=403)
            active.uses_remaining -= 1
            active.save()
            data = {
                "house_number": prop.house_number,
                "contact_phone": prop.contact_phone,
                "caretaker_number": prop.caretaker_number,
                "latitude": prop.latitude,
                "longitude": prop.longitude,
            }
            # optional: create a small notification to admin about the contact view
            return Response(data)

        # if no active payment, expect students number optionally
        students = request.data.get("students")
        if students:
            try:
                students = int(students)
            except Exception:
                return Response({"detail": "Invalid 'students' value."}, status=400)
            
            # Check if students is a positive number
            if students < 1:
                return Response({"detail": "Number of students must be at least 1."}, status=400)
            
            # Check property capacity
            if prop.max_occupancy and students > prop.max_occupancy:
                return Response({
                    "detail": f"This house does not have space for {students} people. Maximum occupancy is {prop.max_occupancy}. Please try another house or enter fewer people."
                }, status=400)
            
            total = prop.university.admin_fee_per_head * students
            return Response({
                "detail": "No approved payment found.",
                "payment_instructions": {
                    "amount": total,
                    "instructions": "Send the admin fee to Ecocash Number 078196541 Account Holder: Brian Chinyanga, then submit your payment confirmation via /api/payments/confirm/.",
                },
            }, status=402)

        return Response({"detail": "No approved payment found. Provide 'students' to compute total admin fee or submit a payment confirmation."}, status=402)


# Notification Views
class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
        return Response(data)


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, recipient=request.user)
            notification.is_read = True
            notification.save()
            return Response({"status": "marked as read"})
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=404)
