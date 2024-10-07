from django.contrib.auth.hashers import check_password
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from api import models as api_models

from api.serializer import ProfileSerializer
from api.utils import generate_random_otp, get_user_from_request
from userauths.models import User, Profile
from api import serializer as api_serializer
from environs import Env

env = Env()
env.read_env()


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializer.MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = api_serializer.RegisterSerializer


class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def get_object(self):
        email = self.kwargs['email']
        user = User.objects.filter(email=email).first()
        if user:
            uuidb64 = user.pk
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh.access_token)
            user.refresh_token = refresh_token
            user.otp = generate_random_otp()
            user.save()
            link = f"{env('FRONT_END_ROUTE_URL')}/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"
            merge_data = {"link": link, "username": user.username}
            subject = "Password Reset Email"
            text_body = render_to_string("email/password_reset.txt", merge_data)
            html_body = render_to_string("email/password_reset.html", merge_data)
            msg = EmailMultiAlternatives(subject=subject, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email],
                                         body=text_body)
            msg.attach_alternative(html_body, "text/html")
            msg.send()
            print(link)
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
            return Response({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        old_password = request.data['old_password']
        new_password = request.data['new_password']

        user = User.objects.get(id=user_id)
        if user is not None:
            if check_password(old_password, user.password):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password changed successfully', 'icon': 'success'},
                                status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Old password is incorrect', 'icon': 'warning'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'User not found', 'icon': 'error'}, status=status.HTTP_404_NOT_FOUND)


class UserDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProfileSerializer

    def get_object(self):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        profile = api_models.Profile.objects.get(user=user)
        return profile


class ProfileApiView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ProfileSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user = get_user_from_request(self.request)
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Profile.objects.get(user=user)

    # Delete the old image
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_image = instance.image.path if instance.image else None

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if old_image and 'image' in request.data:
            import os
            if os.path.isfile(old_image):
                os.remove(old_image)

        return Response(serializer.data)




