from rest_framework import generics
from .serializers import RegisterSerializer


class UserRegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
