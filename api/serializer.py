from rest_framework import serializers
from userauths.models import User, Profile


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
