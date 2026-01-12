from rest_framework import serializers
from properties.models import University, Property, Review, Service, City
from payments.models import PaymentConfirmation, AdminFeePayment


class ServiceSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = ('id', 'name', 'slug', 'description', 'image_url', 'background_color', 'text_color', 'property_type', 'order')
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class UniversitySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = University
        fields = ("id", "name", "city", "city_name", "admin_fee_per_head", "latitude", "longitude")


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name")


class PropertySerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    city_name = serializers.CharField(source="city.name", read_only=True)
    university_name = serializers.CharField(source="university.name", read_only=True)
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    sharing_display = serializers.CharField(source="get_sharing_display", read_only=True)

    class Meta:
        model = Property
        fields = (
            "id",
            "title",
            "description",
            "property_type",
            "city",
            "city_name",
            "university",
            "university_name",
            "nightly_price",
            "price_per_month",
            "location",
            "gender",
            "gender_display",
            "sharing",
            "sharing_display",
            "overnight",
            "max_occupancy",
            "thumbnail",
            "average_rating",
            "distance_km",
        )

    def get_average_rating(self, obj):
        qs = obj.reviews.all()
        if not qs.exists():
            return None
        return round(sum(r.rating for r in qs) / qs.count(), 2)

    def get_thumbnail(self, obj):
        img = obj.images.first()
        if img and hasattr(img, 'image'):
            try:
                request = self.context.get('request')
                url = img.image.url
                if request:
                    return request.build_absolute_uri(url)
                return url
            except Exception:
                return None
        return None

    def get_distance_km(self, obj):
        return getattr(obj, "distance_km", None)


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user_username", "user_email", "rating", "comment", "created_at")


class PropertyDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    distance_to_campus_km = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    city_name = serializers.CharField(source="city.name", read_only=True)
    university_name = serializers.CharField(source="university.name", read_only=True)

    class Meta:
        model = Property
        fields = (
            "id",
            "title",
            "description",
            "property_type",
            "city",
            "city_name",
            "university",
            "university_name",
            "location",
            "latitude",
            "longitude",
            "gender",
            "sharing",
            "overnight",
            "amenities",
            "bedrooms",
            "square_meters",
            "nightly_price",
            "price_per_month",
            "thumbnail",
            "images",
            "reviews",
            "average_rating",
            "distance_to_campus_km",
        )

    def get_thumbnail(self, obj):
        img = obj.images.first()
        if img and hasattr(img, 'image'):
            try:
                request = self.context.get('request')
                url = img.image.url
                if request:
                    return request.build_absolute_uri(url)
                return url
            except Exception:
                return None
        return None

    def get_images(self, obj):
        request = self.context.get('request')
        out = []
        for img in obj.images.all():
            try:
                url = img.image.url
                if request:
                    url = request.build_absolute_uri(url)
            except Exception:
                url = None
            out.append({"id": img.id, "image": url})
        return out

    def get_average_rating(self, obj):
        qs = obj.reviews.all()
        if not qs.exists():
            return None
        return round(sum(r.rating for r in qs) / qs.count(), 2)

    def get_distance_to_campus_km(self, obj):
        uni = obj.university
        if not (uni and uni.latitude and uni.longitude and obj.latitude and obj.longitude):
            return None
        import math
        R = 6371
        phi1 = math.radians(float(uni.latitude))
        phi2 = math.radians(float(obj.latitude))
        dphi = math.radians(float(obj.latitude) - float(uni.latitude))
        dlambda = math.radians(float(obj.longitude) - float(uni.longitude))
        a = math.sin(dphi/2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 2)


class PropertyContactSerializer(serializers.ModelSerializer):
    google_map_link = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ("house_number", "contact_phone", "caretaker_number", "latitude", "longitude", "google_map_link")

    def get_google_map_link(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://www.google.com/maps/search/?api=1&query={obj.latitude},{obj.longitude}"
        return ""

class PaymentConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentConfirmation
        fields = ("id", "payment", "confirmation_text", "status", "submitted_at")
        read_only_fields = ("status", "submitted_at")


class CreatePaymentConfirmationSerializer(serializers.Serializer):
    university = serializers.IntegerField()
    for_number_of_students = serializers.IntegerField(min_value=1)
    confirmation_text = serializers.CharField()

    def validate_university(self, value):
        try:
            uni = University.objects.get(pk=value)
        except University.DoesNotExist:
            raise serializers.ValidationError("University does not exist")
        return uni

    def create(self, validated_data):
        from core.models import Notification
        from django.contrib.auth import get_user_model
        
        user = self.context["request"].user
        university = validated_data["university"]
        num = validated_data["for_number_of_students"]
        amount = university.admin_fee_per_head * num
        payment = AdminFeePayment.objects.create(
            user=user,
            university=university,
            amount=amount,
            for_number_of_students=num,
        )
        confirmation = PaymentConfirmation.objects.create(payment=payment, confirmation_text=validated_data["confirmation_text"])
        
        # Notify all admin users
        User = get_user_model()
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                title="New Payment Confirmation",
                message=f"{user.email} submitted a payment confirmation for {university.name}. Amount: ${amount}. Please review and approve."
            )
        
        return confirmation

    def to_representation(self, instance):
        # instance is a PaymentConfirmation
        return PaymentConfirmationSerializer(instance).data
