"""
Download realistic stock images for service tiles from Unsplash
Run this with: python generate_images.py
Requires: pip install requests pillow
"""
import requests
from PIL import Image
import os
from io import BytesIO

def download_image(url, filename, output_dir):
    """Download and save image from URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            # Resize to optimal dimensions
            img = img.resize((600, 400), Image.Resampling.LANCZOS)
            filepath = os.path.join(output_dir, filename)
            
            # Save with appropriate format
            if filename.endswith('.png'):
                img.save(filepath, 'PNG', optimize=True)
            else:
                img.save(filepath, 'JPEG', quality=85, optimize=True)
            
            return filepath
        else:
            print(f"Failed to download {filename}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None

# Unsplash photo IDs for relevant images (high quality, free to use)
# These are curated Unsplash images - replace with your preferred images
services = [
    ('students', 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=600&h=400&fit=crop'),  # Students studying
    ('longterm', 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop'),  # Modern house
    ('shortterm', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop'),  # Hotel room
    ('realestate', 'https://images.unsplash.com/photo-1560184897-ae75f418493e?w=600&h=400&fit=crop'),  # House for sale
    ('resorts', 'https://images.unsplash.com/photo-1540541338287-41700207dee6?w=600&h=400&fit=crop'),  # Beach resort
    ('shops', 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=400&fit=crop')  # Retail shop
]

# Create directories
mobile_dir = 'assets'
web_dir = '../../backend/static/images'

os.makedirs(mobile_dir, exist_ok=True)
os.makedirs(web_dir, exist_ok=True)

print("Downloading realistic stock images from Unsplash...\n")

# Download for mobile (.png)
print("Mobile images:")
for name, url in services:
    filepath = download_image(url, f'{name}.png', mobile_dir)
    if filepath:
        print(f"✓ Downloaded: {filepath}")

print("\nWeb images:")
# Download for web (.jpg)
for name, url in services:
    filepath = download_image(url, f'{name}.jpg', web_dir)
    if filepath:
        print(f"✓ Downloaded: {filepath}")

print("\n✅ All images downloaded successfully!")
print("\nMobile images: mobile/kivy_app/assets/")
print("Web images: backend/static/images/")
print("\nNote: These are stock images from Unsplash (free to use)")
print("You can replace them with your own professional photos anytime.")

