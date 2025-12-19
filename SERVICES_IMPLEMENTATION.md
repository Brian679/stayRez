# Dynamic Services Implementation

## Overview
Services are now loaded dynamically from the database instead of being hardcoded in templates and mobile app.

## Changes Made

### 1. Database Model
- Created `Service` model in [properties/models.py](backend/properties/models.py)
- Fields: name, slug, description, image, background_color, text_color, is_active, order, property_type
- Registered in Django admin with ordering and filtering

### 2. API Endpoint
- Added `/api/services/` endpoint in [api/urls.py](backend/api/urls.py)
- Created `ServiceSerializer` and `ServiceListView` in [api/serializers.py](backend/api/serializers.py) and [api/views.py](backend/api/views.py)
- Returns JSON with service data including image URLs

### 3. Web Integration
- Updated [web/views.py](backend/web/views.py) `home()` function to fetch services from database
- Services are queried with `Service.objects.filter(is_active=True)`
- Fallback to static images if no image uploaded

### 4. Mobile App Integration
- Updated [main.py](mobile/kivy_app/main.py) `HomeScreen` class
- Services loaded via UrlRequest to `/api/services/`
- Tiles created dynamically with `create_service_tile()` method
- Supports custom colors, images, and navigation

### 5. Management Command
- Created `populate_services` command in [properties/management/commands/populate_services.py](backend/properties/management/commands/populate_services.py)
- Run with: `python manage.py populate_services`
- Populates initial 6 services with existing data

## Usage

### Adding New Services
1. Go to Django admin: `/admin/properties/service/`
2. Click "Add Service"
3. Fill in:
   - Name: Display name
   - Slug: URL-friendly identifier (auto-generated)
   - Description: Short description text
   - Image: Upload image (600x400px recommended)
   - Background Color: Hex color (e.g., #000000)
   - Text Color: Hex color (e.g., #ffffff)
   - Property Type: Link to property type filter
   - Order: Display order (lower = first)
   - Is Active: Enable/disable service

### Updating Services
- Edit any service in admin panel
- Changes reflect immediately on web and mobile
- No code changes needed

### Image Management
- Upload images via admin panel OR
- Place static images in `static/images/{slug}.jpg` as fallback
- Mobile uses `image_url` from API or falls back to `assets/{slug}.png`

## Benefits
✅ No hardcoded service data in code
✅ Easy to add/remove/reorder services via admin
✅ Centralized service management
✅ Support for custom colors and images
✅ Same data source for web and mobile
