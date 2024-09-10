from django.shortcuts import render
from api import serializer as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics

from userauths.models import User, Profile
from rest_framework.permissions import AllowAny


# Define a custom view for obtaining JWT tokens
class MyTokenObtainPairView(TokenObtainPairView):
    # Specify the custom serializer to use for this view
    serializer_class = api_serializer.MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = api_serializer.RegisterSerializer
