from django.contrib import admin
from .models import University, City, Property, PropertyImage, Review, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'slug', 'is_active', 'background_color', 'text_color')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    list_display_links = ('name',)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'admin_fee_per_head', 'latitude', 'longitude')
    search_fields = ('name', 'city__name')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3  # Show 3 empty image upload fields by default
    fields = ('image',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "property_type", "city", "university", "max_occupancy", "is_approved", "is_available")
    list_filter = ("property_type", "is_approved", "is_available", "city", "gender", "sharing")
    search_fields = ("title", "description")
    readonly_fields = ("created_at",)
    inlines = [PropertyImageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("property", "user", "rating", "created_at")
