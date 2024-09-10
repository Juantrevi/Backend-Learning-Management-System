from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token
from django.contrib.auth.password_validation import validate_password

from userauths.models import User, Profile


# This custom serializer allows you to include additional
# user information in the JWT token, which can be useful
# for client-side applications that need to display user details.
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    # Override the get_token method to customize the token payload
    @classmethod
    def get_token(cls, user):
        # Call the parent class's get_token method to get the default token
        token = super().get_token(user)

        # Add custom claims to the token payload
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username

        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'password2']

    def validate(self, attr):
        if attr['password'] != attr['password2']:
            raise serializers.ValidationError({"password": "Password fields do not match"})

        return attr

    def create(self, validated_data):
        user = User.objects.create(
            full_name = validated_data['full_name'],
            email = validated_data['email'],
        )

        email_username, _ = user.email.split('@')
        user.username = email_username
        user.set_password(validated_data['password1'])
        user.save()

        return user


# In this example, UserSerializer and
# ProfileSerializer act as DTOs by
# specifying only a subset of fields
# to be serialized and deserialized.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
