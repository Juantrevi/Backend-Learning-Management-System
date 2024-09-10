from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token

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
