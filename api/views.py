import random

from django.shortcuts import render
from rest_framework.response import Response

from api import serializer as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status

from userauths.models import User, Profile
from rest_framework.permissions import AllowAny

from rest_framework_simplejwt.tokens import RefreshToken

import os
from environs import Env
env = Env()
env.read_env()


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


def generate_random_otp(length=7):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    # Allow any user to access this view (no authentication required)
    permission_classes = [AllowAny]
    # Specify the serializer to use for this view
    serializer_class = api_serializer.UserSerializer

    # Method to get the user object based on the email provided in the URL
    def get_object(self):
        # Get the email from the URL parameters
        email = self.kwargs['email']

        # Find the user with the given email
        user = User.objects.filter(email=email).first()

        # If the user exists
        if user:
            # Get the user's primary key (UUID)
            uuidb64 = user.pk
            # Generate a new JWT refresh token for the user
            refresh = RefreshToken.for_user(user)
            # Convert the refresh token to a string
            refresh_token = str(refresh.access_token)
            # Set the user's refresh token
            user.refresh_token = refresh_token
            # Generate a random OTP (One-Time Password)
            user.otp = generate_random_otp()

            # Save the user object with the new OTP and refresh token
            user.save()

            # Create a link for the password reset page with the OTP, UUID, and refresh token as query parameters
            link = f"{env('ROOT_URL')}/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"
            # Print the link (for debugging purposes)
            print(link)

        # Return the user object
        return user


class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def create(self, request, *args, **kwargs):
        payload = request.data

        otp = payload['otp']
        uuidb64 = payload['uuidb64']
        password = payload['password']

        user = User.objects.get(id=uuidb64, otp=otp)
        if user:
            user.set_password(password)
            user.otp = ""
            user.save()

            return Response({"message": "Password changed successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "User does not exists"}, status=status.HTTP_404_NOT_FOUND)
