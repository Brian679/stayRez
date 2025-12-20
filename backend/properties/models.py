from django.db import models
from django.conf import settings


class Service(models.Model):
    """Dynamic service categories for home screen"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    background_color = models.CharField(max_length=20, default='#eeeeee')
    text_color = models.CharField(max_length=20, default='#333333')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    property_type = models.CharField(max_length=50, blank=True)  # links to Property.PROPERTY_TYPE
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class University(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey("City", on_delete=models.SET_NULL, null=True, blank=True)
    admin_fee_per_head = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # campus coordinates for distance calculations
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Property(models.Model):
    PROPERTY_TYPE = (
        ("students", "Students Accommodation"),
        ("long_term", "Long Term"),
        ("short_term", "Short Term"),
        ("real_estate", "Real Estate"),
        ("resort", "Resort"),
        ("shop", "Shop"),
    )

    GENDER = (
        ("all", "All"),
        ("boys", "Boys only"),
        ("girls", "Girls only"),
        ("mixed", "Mixed Gender"),
    )

    SHARING = (
        ("single", "Single room"),
        ("two", "2 Sharing"),
        ("other", "Other"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    property_type = models.CharField(max_length=30, choices=PROPERTY_TYPE)
    is_approved = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Location (visible only after admin fee payment)
    location = models.CharField(max_length=255, blank=True, help_text="Street address or area name")
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    house_number = models.CharField(max_length=100, blank=True)
    caretaker_number = models.CharField(max_length=50, blank=True)

    # filters and room info
    gender = models.CharField(max_length=10, choices=GENDER, default="all")
    overnight = models.BooleanField(default=False)
    sharing = models.CharField(max_length=10, choices=SHARING, default="single")

    # Pricing
    nightly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Amenities (comma-separated for simple search)
    amenities = models.TextField(blank=True, help_text="Comma-separated amenities (e.g., WiFi,Parking,Kitchen)")
    
    # Property-type specific fields
    # For students accommodation
    max_occupancy = models.IntegerField(null=True, blank=True, help_text="Maximum number of people this property can accommodate")
    distance_to_campus_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # For real estate
    square_meters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    
    # For resorts
    rating_stars = models.IntegerField(null=True, blank=True, help_text="1-5 stars")
    all_inclusive = models.BooleanField(default=False)
    
    # For shops
    shop_category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="properties/")


class Review(models.Model):
    property = models.ForeignKey(Property, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user} - {self.rating}"
