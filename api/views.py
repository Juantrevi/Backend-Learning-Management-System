from django.shortcuts import render
from api import serializer as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics

from userauths.models import User, Profile
from rest_framework.permissions import AllowAny


# This view is used to obtain JSON Web Tokens (JWT)
# for user authentication. It uses a custom serializer
# to include additional user information in the token.
class MyTokenObtainPairView(TokenObtainPairView):
    # Specify the custom serializer to use for this view
    serializer_class = api_serializer.MyTokenObtainPairSerializer


# handles user registration. It allows anyone
# to create a new user account by providing
# the necessary information
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # Allow any user to access this view (no authentication required)
    permission_classes = [AllowAny]
    # Specify the serializer to use for this view
    serializer_class = api_serializer.RegisterSerializer
