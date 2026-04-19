from django.db import models


class Feedback(models.Model):
    # Basic info
    name = models.CharField(max_length=100, blank=True)
    age = models.CharField(max_length=20, blank=True)  # e.g. "Below 18", "18–25", etc.
    gender = models.CharField(
        max_length=20, blank=True
    )  # Male, Female, Prefer not to say
    occupation = models.CharField(
        max_length=50, blank=True
    )  # Student, Tenant, Landlord, Real Estate Agent, Other
    occupation_other = models.CharField(
        max_length=100, blank=True
    )  # If occupation is "Other"
    city = models.CharField(max_length=50, blank=True)  # Harare, Chinhoyi, etc.

    # Internet and usage
    has_internet = models.CharField(max_length=10, blank=True)  # Yes, No
    online_search_freq = models.CharField(
        max_length=20, blank=True
    )  # Never, Rarely, Sometimes, Often, Always
    current_methods_rating = models.CharField(
        max_length=20, blank=True
    )  # Very Poor, Poor, Fair, Good, Excellent

    # Challenges (comma-separated)
    challenges = models.TextField(
        blank=True
    )  # e.g. "Lack of accurate information,No location/map visualization"

    # Ratings (1-5 scale)
    easy_to_use = models.IntegerField(
        null=True, blank=True
    )  # The platform is easy to use
    user_friendly = models.IntegerField(
        null=True, blank=True
    )  # The interface is user-friendly
    quick_response = models.IntegerField(
        null=True, blank=True
    )  # The system responds quickly
    easy_search = models.IntegerField(
        null=True, blank=True
    )  # It is easy to search for properties

    # Text feedback
    like_most = models.TextField(
        blank=True
    )  # What did you like most about the platform?
    challenges_exp = models.TextField(blank=True)  # What challenges did you experience?
    improvements = models.TextField(blank=True)  # What improvements would you suggest?

    # Legacy fields (keeping for backward compatibility)
    user_type = models.CharField(
        max_length=30, blank=True
    )  # For backward compatibility
    ui_review = models.IntegerField(null=True, blank=True)  # Maps to user_friendly
    ux_review = models.IntegerField(null=True, blank=True)  # Maps to easy_to_use
    satisfaction = models.IntegerField(
        null=True, blank=True
    )  # Could be calculated from ratings
    recommend = models.IntegerField(null=True, blank=True)  # Not in current form

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name or 'Anonymous'} at {self.submitted_at}"
