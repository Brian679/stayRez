from django.db import models
from django.conf import settings
from properties.models import Property, University


class AdminFeePayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    for_number_of_students = models.PositiveIntegerField(default=1)
    # number of different accommodation contacts this payment allows (spec requirement = 3)
    allowed_accommodations = models.PositiveIntegerField(default=3)
    # remaining uses left; set when admin approves the payment
    uses_remaining = models.IntegerField(default=0)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def activate(self, days_valid=90):
        from django.utils import timezone
        self.uses_remaining = self.allowed_accommodations
        self.valid_until = timezone.now() + timezone.timedelta(days=days_valid)
        self.save()

    def is_active(self):
        from django.utils import timezone
        if self.uses_remaining > 0:
            if self.valid_until and self.valid_until < timezone.now():
                return False
            return True
        return False

    def __str__(self):
        return f"{self.user.email} - {self.university.name} - {self.amount} (uses left: {self.uses_remaining})"


class PaymentConfirmation(models.Model):
    STATUS = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("declined", "Declined"),
    )
    payment = models.ForeignKey(AdminFeePayment, on_delete=models.CASCADE, related_name="confirmations")
    confirmation_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    def __str__(self):
        return f"Confirmation for {self.payment} - {self.status}"


class ContactView(models.Model):
    """Track which properties a user has viewed contact details for"""
    payment = models.ForeignKey(AdminFeePayment, on_delete=models.CASCADE, related_name="contact_views")
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['payment', 'property']
    
    def __str__(self):
        return f"{self.payment.user.email} viewed {self.property.title}"
