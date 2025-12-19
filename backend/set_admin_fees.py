import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from properties.models import University

# Update all universities to have a default admin fee
universities = University.objects.all()
for uni in universities:
    print(f"{uni.id}: {uni.name} - Current admin_fee_per_head: ${uni.admin_fee_per_head}")
    if uni.admin_fee_per_head == 0:
        uni.admin_fee_per_head = 5.00  # Set default to $5 per head
        uni.save()
        print(f"  → Updated to ${uni.admin_fee_per_head}")
    else:
        print(f"  → Already set")

print("\n✓ All universities updated")
