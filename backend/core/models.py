from django.db import models
from django.conf import settings


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.recipient.email} - {self.title}"


class UserUniversityPreference(models.Model):
    """Track which universities users are interested in based on their browsing behavior"""
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    university = models.ForeignKey('properties.University', on_delete=models.CASCADE)
    visit_count = models.IntegerField(default=1)
    last_visited = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['ip_address', 'university']
    
    def __str__(self):
        return f"{self.ip_address} - {self.university.name} ({self.visit_count} visits)"
