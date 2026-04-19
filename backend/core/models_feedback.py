from django.db import models

class Feedback(models.Model):
    satisfaction = models.IntegerField(null=True, blank=True)  # Overall satisfaction (1-5)
    ease_of_use = models.IntegerField(null=True, blank=True)   # Ease of use (1-5)
    recommend = models.IntegerField(null=True, blank=True)     # Would recommend (1-5)
    like_most = models.TextField(blank=True)                  # What did you like most?
    improvements = models.TextField(blank=True)               # Suggestions for improvement
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback at {self.submitted_at}" 