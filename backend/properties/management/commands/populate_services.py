from django.core.management.base import BaseCommand
from properties.models import Service
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Populate initial services with existing images'

    def handle(self, *args, **kwargs):
        services_data = [
            {
                'name': 'Students Accommodation',
                'slug': 'students',
                'description': 'Are you looking for off campus accommodation',
                'background_color': '#000000',
                'text_color': '#ffd700',
                'property_type': 'students',
                'order': 1,
            },
            {
                'name': 'Long-term Accommodation',
                'slug': 'longterm',
                'description': 'Looking for 1, 2 or 3 rooms up to full houses to rent',
                'background_color': '#eeeeee',
                'text_color': '#333333',
                'property_type': 'long_term',
                'order': 2,
            },
            {
                'name': 'Short-term Accommodation',
                'slug': 'shortterm',
                'description': 'Perfect for short stays and temporary housing needs',
                'background_color': '#eeeeee',
                'text_color': '#333333',
                'property_type': 'short_term',
                'order': 3,
            },
            {
                'name': 'Real Estate',
                'slug': 'realestate',
                'description': 'Buy or sell properties with ease',
                'background_color': '#eeeeee',
                'text_color': '#333333',
                'property_type': 'real_estate',
                'order': 4,
            },
            {
                'name': 'Resorts',
                'slug': 'resorts',
                'description': 'Discover amazing vacation destinations',
                'background_color': '#eeeeee',
                'text_color': '#333333',
                'property_type': 'resort',
                'order': 5,
            },
            {
                'name': 'Shops to Rent',
                'slug': 'shops',
                'description': 'Commercial spaces for your business',
                'background_color': '#eeeeee',
                'text_color': '#333333',
                'property_type': 'shop',
                'order': 6,
            },
        ]

        for data in services_data:
            slug = data['slug']
            service, created = Service.objects.update_or_create(
                slug=slug,
                defaults=data
            )
            
            # Link existing image if available
            image_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR / 'static', 'images', f'{slug}.jpg')
            if os.path.exists(image_path) and not service.image:
                # Note: For actual image upload, you'd need to handle file copying
                # For now, we'll use static images via image_url in serializer
                pass
            
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{status} service: {service.name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(services_data)} services'))
