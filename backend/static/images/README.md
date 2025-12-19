# Static Images Folder

This folder contains images for the home page service cards.

## Required Images:

1. **students.jpg** - Students accommodation (e.g., dorm rooms, student housing, university campus)
2. **longterm.jpg** - Long-term accommodation (e.g., houses, apartments, residential buildings)
3. **shortterm.jpg** - Short-term accommodation (e.g., hotel rooms, temporary housing, Airbnb)
4. **realestate.jpg** - Real estate (e.g., house for sale, real estate sign, property listings)
5. **resorts.jpg** - Resorts (e.g., beach resort, vacation destination, luxury hotels)
6. **shops.jpg** - Shops to rent (e.g., commercial storefront, retail spaces, shopping centers)

## Image Specifications:

- **Format:** JPG or PNG
- **Recommended size:** 600x400 pixels (3:2 aspect ratio)
- **Quality:** High resolution for web display
- **File size:** Optimize for web (under 200KB per image)
- **Style:** Consistent visual style across all images

## Django Static Files Setup:

Make sure your `settings.py` includes:

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
```

## Usage:

Images will be displayed in the home page service cards at 180px height with object-fit: cover.

If an image fails to load, the card will still display with just the title and description.

## Placeholder Note:

Add your images to this folder with the exact filenames listed above. You can use free stock photo sites like:
- Unsplash.com
- Pexels.com
- Pixabay.com
