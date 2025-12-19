import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from properties.models import University

# Zimbabwe university coordinates
university_coords = {
    'University of Zimbabwe': {'lat': -17.7840, 'lon': 31.0534},
    'Midlands State University': {'lat': -19.4375, 'lon': 29.8111},
    'National University of Science and Technology': {'lat': -20.1531, 'lon': 28.5861},
    'Chinhoyi University of Technology': {'lat': -17.3667, 'lon': 30.2000},
    'Bindura University of Science Education': {'lat': -17.3011, 'lon': 31.3314},
    'Great Zimbabwe University': {'lat': -20.2689, 'lon': 30.9339},
    'Africa University': {'lat': -18.9167, 'lon': 32.6667},
    'Harare Institute of Technology': {'lat': -17.8252, 'lon': 31.0335},
}

unis = University.objects.all()
for uni in unis:
    print(f"\nUniversity: {uni.name}")
    print(f"  Current: lat={uni.latitude}, lon={uni.longitude}")
    
    if not uni.latitude or not uni.longitude:
        # Try to find matching coordinates
        for name, coords in university_coords.items():
            if name.lower() in uni.name.lower() or uni.name.lower() in name.lower():
                uni.latitude = coords['lat']
                uni.longitude = coords['lon']
                uni.save()
                print(f"  ✓ Updated to: lat={uni.latitude}, lon={uni.longitude}")
                break
        else:
            # Default to Harare city center if no match found
            uni.latitude = -17.8292
            uni.longitude = 31.0522
            uni.save()
            print(f"  ✓ Set to Harare center: lat={uni.latitude}, lon={uni.longitude}")
    else:
        print(f"  Already set")

print("\n✓ Done updating university coordinates")
