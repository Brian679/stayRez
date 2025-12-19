import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from payments.models import AdminFeePayment, PaymentConfirmation

# Find all approved payment confirmations
approved_confirmations = PaymentConfirmation.objects.filter(status='approved')

print(f"Found {approved_confirmations.count()} approved payment confirmations")

for confirmation in approved_confirmations:
    payment = confirmation.payment
    print(f"\nPayment ID: {payment.id}")
    print(f"  User: {payment.user.email}")
    print(f"  University: {payment.university.name}")
    print(f"  Current uses_remaining: {payment.uses_remaining}")
    
    if payment.uses_remaining == 0:
        print(f"  Activating payment...")
        payment.activate()
        print(f"  New uses_remaining: {payment.uses_remaining}")
    else:
        print(f"  Already activated")

print("\n✓ Done")
