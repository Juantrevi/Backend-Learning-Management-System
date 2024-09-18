import random

from django.db.utils import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser
from rest_framework_simplejwt.tokens import Token
from django.contrib.auth.password_validation import validate_password
from api import models as api_models
import re

from userauths.models import User, Profile


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
        This custom serializer allows you to include additional
        user information in the JWT token, which can be useful
        for client-side applications that need to display user details.
    """

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
    """
        Class used to register a new user
        inherits from serializers.ModelSerializer
    """
    # Define two password fields, one for the password and one for confirmation
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    # Meta class to specify the model and fields to be used
    class Meta:
        # Use the custom User model
        model = User
        # Fields to be included in the serializer
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']

    # Validate method to check if the passwords match
    def validate(self, attr):
        # Transform email to lowercase
        attr['email'] = attr['email'].lower()

        # Check for blank spaces in the password
        if ' ' in attr['password']:
            raise serializers.ValidationError({"password": "Password should not contain spaces"})

        # Correct the name fields
        for field in ['first_name', 'last_name']:
            # Remove leading and trailing spaces, and ensure only one space between words
            attr[field] = re.sub(r'\s+', ' ', attr[field].strip())
            # Capitalize the first letter of each word
            attr[field] = ' '.join(word.capitalize() for word in attr[field].split(' '))

        # Check if the two password fields match
        if attr['password'] != attr['password2']:
            raise serializers.ValidationError({"password": "Password fields do not match"})

        return attr

    def create(self, validated_data):
        """
            Creates a new user with the provided data.
            It sets the username to the part of the email
            before the "@" symbol and sets the user's password.
            Finally, it saves the user to the database and returns
            the created user
        """
        # Extract the part before the "@" symbol from the email to use as the username
        email_username, _ = validated_data['email'].split('@')

        # Create a new user with the provided full name and email
        user = User.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            full_name=f"{validated_data['first_name']} {validated_data['last_name']}",
            email=validated_data['email'],
            username=f"{email_username}{random.randint(1000, 9999)}"
        )

        user.set_password(validated_data['password'])
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


# ---------MODEL SERIALIZERS----------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['title', 'image', 'slug', 'course_count']
        model = api_models.Category


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['user', 'image', 'full_name', 'bio', 'facebook', 'x', 'linkedin', 'about', 'country', 'students',
                  'courses', 'review']
        model = api_models.Teacher


class VariantItemSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.VariantItem


class VariantSerializer(serializers.ModelSerializer):
    variant_items = VariantItemSerializer()

    class Meta:
        fields = '__all__'
        model = api_models.Variant


class QuestionAnswerMessageSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.QuestionAnswerMessage


class QuestionAnswerSerializer(serializers.ModelSerializer):
    messages = QuestionAnswerMessageSerializer(many=True)
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.QuestionAnswer


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.Cart


class CartOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.CartOrderItem


class CartOrderSerializer(serializers.ModelSerializer):
    order_items = CartOrderItemSerializer(many=True)

    class Meta:
        fields = '__all__'
        model = api_models.CartOrder


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.Certificate


class CompletedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.CompletedLesson


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.Note


class ReviewSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False)

    class Meta:
        fields = '__all__'
        model = api_models.Review


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.Notification


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.Coupon


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.WishList


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = api_models.Country


class EnrolledCourseSerializer(serializers.ModelSerializer):
    lectures = VariantItemSerializer(many=True, read_only=True)
    completed_lesson = CompletedLessonSerializer(many=True, read_only=True)
    curriculum = VariantItemSerializer(many=True, read_only=True)
    note = NoteSerializer(many=True, read_only=True)
    question_answer = QuestionAnswerSerializer(many=True, read_only=True)
    review = ReviewSerializer(many=True, read_only=True)

    class Meta:
        fields = '__all__'
        model = api_models.EnrolledCourse

    def __init__(self, *args, **kwargs):
        """This method ensures that when I serialize
        a Course object, the related Teacher object is
        included in the serialized data, allowing to
         see the teacher's name in the frontend."""
        super(EnrolledCourseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class CourseSerializer(serializers.ModelSerializer):
    # students will become an array of students
    """CourseSerializer class is a model serializer
     for the Course model, which includes various fields
      and related objects."""

    students = EnrolledCourseSerializer(many=True)
    curriculum = VariantItemSerializer(many=True)
    lectures = VariantItemSerializer(many=True)
    reviews = ReviewSerializer(many=True)

    class Meta:
        fields = [
            # fields
            'category',
            'teacher',
            'image',
            'file',
            'title',
            'description',
            'price',
            'language',
            'level',
            'platform_status',
            'teacher_course_status',
            'featured',
            'course_id',
            'slug',
            'date',
            # methods
            'students',
            'curriculum',
            'lectures',
            'average_rating',
            'rating_count',
            'reviews'
        ]
        model = api_models.Course

    def __init__(self, *args, **kwargs):
        """This method ensures that when I serialize
        a Course object, the related Teacher object is
        included in the serialized data, allowing to
         see the teacher's name in the frontend."""
        super(CourseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3
