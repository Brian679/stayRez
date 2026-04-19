from rest_framework import serializers
from core.models_feedback import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            "name",
            "age",
            "gender",
            "occupation",
            "occupation_other",
            "city",
            "has_internet",
            "online_search_freq",
            "current_methods_rating",
            "challenges",
            "easy_to_use",
            "user_friendly",
            "quick_response",
            "easy_search",
            "like_most",
            "challenges_exp",
            "improvements",
            "submitted_at",
        ]
