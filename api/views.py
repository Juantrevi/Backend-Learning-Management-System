import random
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from api import serializer as api_serializer
from userauths.models import User, Profile
from api import models as api_models

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from decimal import Decimal

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
            link = f"{env('FRONT_END_ROUTE_URL')}/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"

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


class CategoryListAPIView(generics.ListAPIView):
    queryset = api_models.Category.objects.filter(active=True)
    serializer_class = api_serializer.CategorySerializer
    # TODO: Change the permission
    permission_classes = [AllowAny]


class CourseListAPIView(generics.ListAPIView):
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
    serializer_class = api_serializer.CourseSerializer
    # TODO: Change the permission
    permission_classes = [AllowAny]


class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CourseSerializer
    # TODO: Change the permission
    permission_classes = [AllowAny]

    # Override the course method to get it by it's slug
    def get_object(self):
        slug = self.kwargs['slug']
        course = api_models.Course.objects.get(slug=slug, platform_status="Published",
                                               teacher_course_status="Published")
        return course


"""
Handles the creation and updating of cart items. 
Provides a default implementation for 
creating a model instance.

-Class Definition: CartAPIView inherits from CreateAPIView.
-Queryset and Serializer: Specifies the 
    queryset and serializer class.
-Create Method: Custom logic to handle the 
    creation and updating of cart items based 
    on the request data.
"""


# Define the CartAPIView class, which inherits from CreateAPIView
class CartAPIView(generics.CreateAPIView):
    # Set the queryset to all Cart objects
    queryset = api_models.Cart.objects.all()
    # Set the serializer class to CartSerializer
    serializer_class = api_serializer.CartSerializer
    # Allow any user to access this view (no authentication required)
    permission_classes = [AllowAny]

    # Override the create method to handle custom logic for creating/updating cart items
    def create(self, request, *args, **kwargs):
        """
        # IMPORTANT!
        # From the FE YOU NEED TO PASS the course_id, user_id, price,
        country_name, cart_id in a payload to this API, something like:
        {
          "price": "100",
          "country_name": "United States",
          "cart_id": "2131241",
          "date": "2024-09-13T23:05:32.519Z",
          "course_id": 1,
          "user_id": 1
        }
        """
        # Extract data from the request payload
        course_id = request.data['course_id']
        user_id = request.data['user_id']
        price = request.data['price']
        country_name = request.data['country_name']
        cart_id = request.data['cart_id']

        # Retrieve the course object based on the provided course_id
        course = api_models.Course.objects.filter(id=course_id).first()

        # Retrieve the user object based on the provided user_id, if it's not "undefined"
        if user_id != "undefined":
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        # Retrieve the country object based on the provided country_name
        try:
            country_object = api_models.Country.objects.filter(name=country_name).first()
            country = country_object.name
        except:
            country_object = None
            country = "USA"

        # Calculate the tax rate based on the country object
        if country_object:
            tax_rate = country_object.tax_rate / 100
        else:
            tax_rate = 0

        # Check if a cart item already exists for the given cart_id and course
        cart = api_models.Cart.objects.filter(cart_id=cart_id, course=course).first()

        if cart:
            # If the cart item exists, update its details
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()

            # Return a success response indicating the cart was updated
            return Response({"message": "Cart updated Successfully"}, status=status.HTTP_200_OK)
        else:
            # If the cart item does not exist, create a new one
            cart = api_models.Cart()
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()

            # Return a success response indicating the cart was created
            return Response({"message": "Cart created Successfully"}, status=status.HTTP_201_CREATED)


# generics. -> ListAPIView, RetrieveAPIView, CreateAPIView


class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset


class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs['cart_id']
        """It is just the ID of the item 
        that we want to delete, be careful 
        on the second parameter"""
        item_id = self.kwargs['item_id']

        return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()


# Cart Statistics API View
class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]
    # This API by default will be expecting this field
    lookup_field = 'cart_id'

    @staticmethod
    def calculate_price(cart_item):
        return cart_item.price

    @staticmethod
    def calculate_tax(cart_item):
        return cart_item.tax_fee

    @staticmethod
    def calculate_total(cart_item):
        return cart_item.total

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        queryset = api_models.Cart.objects.filter(cart_id=cart_id)
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_price = 0.00
        total_tax = 0.00
        total_total = 0.00

        """
        Accumulative sums for all the cart
        Total + tax + Total    
        """
        for cart_item in queryset:
            total_price += float(self.calculate_price(cart_item))
            total_tax += float(self.calculate_tax(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2) #Round to 2 decimal places

        data = {
            "price": total_price,
            "tax": total_tax,
            "total": total_total
        }

        return Response(data, status.HTTP_200_OK)

