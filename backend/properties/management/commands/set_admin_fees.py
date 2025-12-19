from django.core.management.base import BaseCommand
from properties.models import University


class Command(BaseCommand):
    help = 'Set default admin fee for all universities'

    def handle(self, *args, **options):
        universities = University.objects.all()
        updated_count = 0
        
        for uni in universities:
            self.stdout.write(f"{uni.id}: {uni.name} - Current admin_fee_per_head: ${uni.admin_fee_per_head}")
            if uni.admin_fee_per_head == 0:
                uni.admin_fee_per_head = 5.00  # Set default to $5 per head
                uni.save()
                self.stdout.write(self.style.SUCCESS(f"  → Updated to ${uni.admin_fee_per_head}"))
                updated_count += 1
            else:
                self.stdout.write(f"  → Already set")
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Updated {updated_count} universities'))
