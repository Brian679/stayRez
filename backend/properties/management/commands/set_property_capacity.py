from django.core.management.base import BaseCommand
from properties.models import Property


class Command(BaseCommand):
    help = 'Set default max_occupancy for properties based on sharing type'

    def handle(self, *args, **options):
        properties = Property.objects.filter(max_occupancy__isnull=True)
        updated_count = 0
        
        for prop in properties:
            # Set default capacity based on sharing type
            if prop.sharing == 'single':
                prop.max_occupancy = 1
            elif prop.sharing == 'two':
                prop.max_occupancy = 2
            else:  # 'other' or any other value
                prop.max_occupancy = 4  # Default to 4 for 'other'
            
            prop.save()
            self.stdout.write(f"{prop.id}: {prop.title} - Set max_occupancy to {prop.max_occupancy} (sharing: {prop.sharing})")
            updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Updated {updated_count} properties'))
