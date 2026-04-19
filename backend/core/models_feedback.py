from django.db import models

class Feedback(models.Model):
    name = models.CharField(max_length=100, blank=True)
    user_type = models.CharField(max_length=30, blank=True)  # e.g. landlord, student
    age = models.CharField(max_length=20, blank=True)
    ui_review = models.IntegerField(null=True, blank=True)   # UI review (1-5)
    ux_review = models.IntegerField(null=True, blank=True)   # UX review (1-5)
    satisfaction = models.IntegerField(null=True, blank=True)  # Overall satisfaction (1-5)
    ease_of_use = models.IntegerField(null=True, blank=True)   # Ease of use (1-5)
    recommend = models.IntegerField(null=True, blank=True)     # Would recommend (1-5)
    like_most = models.TextField(blank=True)                  # What did you like most?
    improvements = models.TextField(blank=True)               # Suggestions for improvement
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name or 'Anonymous'} at {self.submitted_at}" 