from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import PaymentConfirmation
from core.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=PaymentConfirmation)
def notify_admin_on_confirmation(sender, instance, created, **kwargs):
    if created:
        # notify all admin users
        admins = User.objects.filter(role="admin")
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                title="New payment confirmation",
                message=f"User {instance.payment.user.email} submitted a payment confirmation for {instance.payment.university.name}.",
            )


@receiver(pre_save, sender=PaymentConfirmation)
def handle_payment_status_change(sender, instance, **kwargs):
    """Activate payment when status changes to approved"""
    if instance.pk:  # Only for existing objects
        try:
            old_instance = PaymentConfirmation.objects.get(pk=instance.pk)
            # Check if status changed from pending/declined to approved
            if old_instance.status != 'approved' and instance.status == 'approved':
                # Activate the payment
                payment = instance.payment
                payment.activate()
                
                # Notify the user
                Notification.objects.create(
                    recipient=payment.user,
                    title="Payment Approved",
                    message=f"Your payment for {payment.university.name} has been approved! You can now view landlord contacts for up to {payment.allowed_accommodations} accommodations."
                )
        except PaymentConfirmation.DoesNotExist:
            pass
