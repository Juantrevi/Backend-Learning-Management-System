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


# This class inherits from serializers.ModelSerializer and is used to handle user registration.
class RegisterSerializer(serializers.ModelSerializer):
    # Define two password fields, one for the password and one for confirmation
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    # Meta class to specify the model and fields to be used
    class Meta:
        model = User  # Use the custom User model
        fields = ['full_name', 'email', 'password', 'password2']  # Fields to be included in the serializer

    # Validate method to check if the passwords match
    def validate(self, attr):
        # Check if the two password fields match
        if attr['password'] != attr['password2']:
            # Raise a validation error if the passwords do not match
            raise serializers.ValidationError({"password": "Password fields do not match"})
        return attr  # Return the validated data

    # Creates a new user with the provided data.
    # It sets the username to the part of the email
    # before the "@" symbol and sets the user's password.
    # Finally, it saves the user to the database and returns
    # the created user
    def create(self, validated_data):
        # Create a new user with the provided full name and email
        user = User.objects.create(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
        )

        # Extract the part before the "@" symbol from the email to use as the username
        email_username, _ = user.email.split('@')
        user.username = email_username  # Set the username
        user.set_password(validated_data['password'])  # Set the user's password
        user.save()  # Save the user to the database

        return user  # Return the created user


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
