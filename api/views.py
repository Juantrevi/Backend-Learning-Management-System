import random

from django.shortcuts import render
from rest_framework.response import Response

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from api import serializer as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status

from userauths.models import User, Profile
from rest_framework.permissions import AllowAny

from django.conf import settings

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

            # Prepare the data to be used in the email template
            merge_data = {
                "link": link,  # The password reset link
                "username": user.username  # The username of the recipient
            }

            # Set the subject of the email
            subject = "Password Reset Email"

            # Render the plain text version of the email body using the template and merge data
            text_body = render_to_string("email/password_reset.txt", merge_data)

            # Render the HTML version of the email body using the template and merge data
            html_body = render_to_string("email/password_reset.html", merge_data)

            # Create an email message object with the subject, from email, to email, and plain text body
            msg = EmailMultiAlternatives(
                subject=subject,
                from_email=settings.DEFAULT_FROM_EMAIL,  # The sender's email address
                to=[user.email],  # The recipient's email address
                body=text_body  # The plain text body of the email
            )

            # Attach the HTML version of the email body to the message
            msg.attach_alternative(html_body, "text/html")

            # Send the email
            msg.send()

            # Print the link (for debugging purposes)
            print(link)

        # Return the user object
        return user


class PasswordChangeAPIView(generics.CreateAPIView):
    # Allow any user to access this view (no authentication required)
    permission_classes = [AllowAny]
    # Specify the serializer to use for this view
    serializer_class = api_serializer.UserSerializer

    # Handle the POST request to change the user's password
    def create(self, request, *args, **kwargs):
        # Extract the data from the request
        payload = request.data

        # Get the OTP, UUID, and new password from the payload
        otp = payload['otp']
        uuidb64 = payload['uuidb64']
        password = payload['password']

        # Retrieve the user object based on the provided UUID and OTP
        user = User.objects.get(id=uuidb64, otp=otp)
        if user:
            # Set the new password for the user
            user.set_password(password)
            # Clear the OTP
            user.otp = ""
            # Save the user object with the new password
            user.save()

            # Return a success message
            return Response({"message": "Password changed successfully"}, status=status.HTTP_201_CREATED)
        else:
            # Return an error message if the user does not exist
            return Response({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)