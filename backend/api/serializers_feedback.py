from rest_framework import serializers
from core.models_feedback import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'satisfaction',
            'ease_of_use',
            'recommend',
            'like_most',
            'improvements',
            'submitted_at',
        ]
