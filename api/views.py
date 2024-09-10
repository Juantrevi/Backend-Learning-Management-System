from django.shortcuts import render
from api import serializer as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView


# Define a custom view for obtaining JWT tokens
class MyTokenObtainPairView(TokenObtainPairView):
    # Specify the custom serializer to use for this view
    serializer_class = api_serializer.MyTokenObtainPairSerializer
