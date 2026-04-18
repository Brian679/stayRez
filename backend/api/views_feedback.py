from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models_feedback import Feedback
from .serializers_feedback import FeedbackSerializer

class FeedbackCreateView(APIView):
    permission_classes = []  # Allow any user

    def post(self, request, *args, **kwargs):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Thank you for your feedback!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
