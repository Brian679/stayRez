from django.db.models.signals import post_save
from django.dispatch import receiver
from properties.models import Property
from core.models import Notification, UserUniversityPreference


@receiver(post_save, sender=Property)
def notify_property_watchers(sender, instance, created, **kwargs):
    """
    Notify users who have visited this university when a property is added or updated
    """
    if not instance.university:
        return
    
    # Only notify if property is approved
    if not instance.is_approved:
        return
    
    # Get all users who have visited this university
    preferences = UserUniversityPreference.objects.filter(
        university=instance.university,
        user__isnull=False
    ).select_related('user').distinct()
    
    # Create notifications
    for pref in preferences:
        # Skip the property owner
        if pref.user == instance.owner:
            continue
            
        if created:
            title = f"New accommodation at {instance.university.name}"
            message = f"A new property '{instance.title}' has been added at {instance.university.name}. Check it out!"
        else:
            title = f"Accommodation updated at {instance.university.name}"
            message = f"'{instance.title}' at {instance.university.name} has been updated."
        
        Notification.objects.create(
            recipient=pref.user,
            title=title,
            message=message,
            link=f"/property/{instance.id}/"
        )
