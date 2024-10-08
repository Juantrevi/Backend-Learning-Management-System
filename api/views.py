# import logging
# import random
#
# import requests
# from django.core.mail import EmailMultiAlternatives
# from django.http import JsonResponse
# from django.shortcuts import redirect
# from django.template.loader import render_to_string
# from django.conf import settings
# from django.db.models import Avg
# from rest_framework.exceptions import NotFound
#
# from api import serializer as api_serializer
# from api.serializer import EnrolledCourseSerializer
# from userauths.models import User, Profile
# from api import models as api_models
# from django.contrib.auth.hashers import check_password
#
# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework import generics, status
# from rest_framework_simplejwt.tokens import RefreshToken, Token
# from rest_framework.response import Response
# from decimal import Decimal
# from rest_framework import generics
# from rest_framework.permissions import AllowAny
# from .models import EnrolledCourse
# from .utils import get_user_from_request
# import stripe
#
# import os
# from environs import Env
#
# env = Env()
# env.read_env()
#
# stripe.api_key = settings.STRIPE_SECRET_KEY
# PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
# PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID
#
# """
# List of the generic views provided by Django REST Framework and the HTTP methods they correspond to:
#     ListAPIView: GET
#     RetrieveAPIView: GET
#     CreateAPIView: POST
#     UpdateAPIView: PUT, PATCH
#     DestroyAPIView: DELETE
#     ListCreateAPIView: GET, POST
#     RetrieveUpdateAPIView: GET, PUT, PATCH
#     RetrieveDestroyAPIView: GET, DELETE
#     RetrieveUpdateDestroyAPIView: GET, PUT, PATCH, DELETE
# """
#
#
# # UTILITY FUNCTIONS
# def generate_random_otp(length=7):
#     otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
#     return otp
#
#
# class MyTokenObtainPairView(TokenObtainPairView):
#     """
#         This view is used to obtain JSON Web Tokens (JWT)
#         for user authentication. It uses a custom serializer
#         to include additional user information in the token.
#     """
#     # Specify the custom serializer to use for this view
#     serializer_class = api_serializer.MyTokenObtainPairSerializer
#
#
# class RegisterView(generics.CreateAPIView):
#     """
#         Handles user registration. It allows anyone
#         to create a new user account by providing
#         the necessary information
#     """
#     queryset = User.objects.all()
#     # Allow any user to access this view (no authentication required)
#     permission_classes = [AllowAny]
#     # Specify the serializer to use for this view
#     serializer_class = api_serializer.RegisterSerializer
#
#
# class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
#     # Allow any user to access this view (no authentication required)
#     permission_classes = [AllowAny]
#     # Specify the serializer to use for this view
#     serializer_class = api_serializer.UserSerializer
#
#     # Method to get the user object based on the email provided in the URL
#     def get_object(self):
#         # Get the email from the URL parameters
#         email = self.kwargs['email']
#
#         # Find the user with the given email
#         user = User.objects.filter(email=email).first()
#
#         # If the user exists
#         if user:
#             # Get the user's primary key (UUID)
#             uuidb64 = user.pk
#             # Generate a new JWT refresh token for the user
#             refresh = RefreshToken.for_user(user)
#             # Convert the refresh token to a string
#             refresh_token = str(refresh.access_token)
#             # Set the user's refresh token
#             user.refresh_token = refresh_token
#             # Generate a random OTP (One-Time Password)
#             user.otp = generate_random_otp()
#
#             # Save the user object with the new OTP and refresh token
#             user.save()
#
#             # Create a link for the password reset page with the OTP, UUID, and refresh token as query parameters
#             link = f"{env('FRONT_END_ROUTE_URL')}/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"
#
#             # Prepare the data to be used in the email template
#             merge_data = {
#                 "link": link,  # The password reset link
#                 "username": user.username  # The username of the recipient
#             }
#
#             # Set the subject of the email
#             subject = "Password Reset Email"
#
#             # Render the plain text version of the email body using the template and merge data
#             text_body = render_to_string("email/password_reset.txt", merge_data)
#
#             # Render the HTML version of the email body using the template and merge data
#             html_body = render_to_string("email/password_reset.html", merge_data)
#
#             # Create an email message object with the subject, from email, to email, and plain text body
#             msg = EmailMultiAlternatives(
#                 subject=subject,
#                 from_email=settings.DEFAULT_FROM_EMAIL,  # The sender's email address
#                 to=[user.email],  # The recipient's email address
#                 body=text_body  # The plain text body of the email
#             )
#
#             # Attach the HTML version of the email body to the message
#             msg.attach_alternative(html_body, "text/html")
#
#             # Send the email
#             msg.send()
#
#             # Print the link (for debugging purposes)
#             print(link)
#
#         # Return the user object
#         return user
#
#
# class PasswordChangeAPIView(generics.CreateAPIView):
#     # Allow any user to access this view (no authentication required)
#     permission_classes = [AllowAny]
#     # Specify the serializer to use for this view
#     serializer_class = api_serializer.UserSerializer
#
#     # Handle the POST request to change the user's password
#     def create(self, request, *args, **kwargs):
#         # Extract the data from the request
#         payload = request.data
#
#         # Get the OTP, UUID, and new password from the payload (EXPECTED FROM THE FRONTEND)
#         otp = payload['otp']
#         uuidb64 = payload['uuidb64']
#         password = payload['password']
#
#         # Retrieve the user object based on the provided UUID and OTP
#         user = User.objects.get(id=uuidb64, otp=otp)
#         if user:
#             # Set the new password for the user
#             user.set_password(password)
#             # Clear the OTP
#             user.otp = ""
#             # Save the user object with the new password
#             user.save()
#
#             # Return a success message
#             return Response({"message": "Password changed successfully"}, status=status.HTTP_201_CREATED)
#         else:
#             # Return an error message if the user does not exist
#             return Response({"message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
#
#
# class ChangePasswordAPIView(generics.CreateAPIView):
#     serializer_class = api_serializer.UserSerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         user_id = request.data['user_id']
#         old_password = request.data['old_password']
#         new_password = request.data['new_password']
#
#         user = User.objects.get(id=user_id)
#         if user is not None:
#             if check_password(old_password, user.password):
#                 user.set_password(new_password)
#                 user.save()
#                 return Response({'message': 'Password changed successfully', 'icon': 'success'},
#                                 status=status.HTTP_200_OK)
#             else:
#                 return Response({'message': 'Old password is incorrect', 'icon': 'warning'},
#                                 status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'message': 'User not found', 'icon': 'error'}, status=status.HTTP_404_NOT_FOUND)
#
#
# class CategoryListAPIView(generics.ListAPIView):
#     queryset = api_models.Category.objects.filter(active=True)
#     serializer_class = api_serializer.CategorySerializer
#     # TODO: Change the permission
#     permission_classes = [AllowAny]
#
#
# class CourseListAPIView(generics.ListAPIView):
#     queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
#     serializer_class = api_serializer.CourseSerializer
#     # TODO: Change the permission
#     permission_classes = [AllowAny]
#
#
# class BestCoursesListAPIView(generics.ListAPIView):
#     serializer_class = api_serializer.CourseSerializer
#     permission_classes = [AllowAny]
#
#     # TODO: Make the logic so it brings not only
#     #   by rating but a mix between rating and number of reviews
#
#     def get_queryset(self):
#         return api_models.Course.objects.filter(
#             platform_status="Published",
#             teacher_course_status="Published"
#         ).annotate(
#             avg_rating=Avg('review__rating')
#         ).order_by('-avg_rating')[:4]
#
#
# class CourseDetailAPIView(generics.RetrieveAPIView):
#     serializer_class = api_serializer.CourseSerializer
#     # TODO: Change the permission
#     permission_classes = [AllowAny]
#
#     # Override the course method to get it by it's slug
#     def get_object(self):
#         slug = self.kwargs['slug']
#         course = api_models.Course.objects.get(slug=slug, platform_status="Published",
#                                                teacher_course_status="Published")
#         return course
#
#
# class SearchCourseAPIView(generics.ListAPIView):
#     serializer_class = api_serializer.CourseSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         query = self.request.GET.get('query')
#         """Returning:
#             If we have a course called 'learn LMS Systems with django and react'
#             and we just put 'learn LMS' it'll bring the courses that CONTAINS
#             part of the query
#         """
#         return api_models.Course.objects.filter(
#             title__icontains=query,
#             platform_status="Published",
#             teacher_course_status="Published"
#         )
#
#
# class CartAPIView(generics.CreateAPIView):
#     """
#     Handles the creation and updating of cart items.
#     Provides a default implementation for
#     creating a model instance.
#
#     {
#           "course_id": 1,
#           "user_id": 1,
#           "price": "100",
#           "country_name": "United States",
#           "cart_id": "423432"
#     }
#
#     -Class Definition: CartAPIView inherits from CreateAPIView.
#     -Queryset and Serializer: Specifies the
#         queryset and serializer class.
#     -Create Method: Custom logic to handle the
#         creation and updating of cart items based
#         on the request data.
#     """
#     # Set the queryset to all Cart objects
#     queryset = api_models.Cart.objects.all()
#     # Set the serializer class to CartSerializer
#     serializer_class = api_serializer.CartSerializer
#     # Allow any user to access this view (no authentication required)
#     permission_classes = [AllowAny]
#
#     # Override the create method to handle custom logic for creating/updating cart items
#     def create(self, request, *args, **kwargs):
#         """
#         # IMPORTANT!
#         # From the FE YOU NEED TO PASS the course_id, user_id, price,
#         country_name, cart_id in a payload to this API, something like:
#         {
#           "course_id": 1,
#           "user_id": 1,
#           "price": "100",
#           "country_name": "United States",
#           "cart_id": "423432"
#         }
#         """
#         # Extract data from the request payload
#         course_id = request.data['course_id']
#         user_id = request.data['user_id']
#         price = request.data['price']
#         country_name = request.data['country_name']
#         cart_id = request.data['cart_id']
#
#         # Retrieve the course object based on the provided course_id
#         course = api_models.Course.objects.filter(id=course_id).first()
#
#         # Retrieve the user object based on the provided user_id, if it's not "undefined"
#         if user_id != "undefined":
#             user = User.objects.filter(id=user_id).first()
#         else:
#             user = None
#
#         # Retrieve the country object based on the provided country_name
#         try:
#             country_object = api_models.Country.objects.filter(name=country_name).first()
#             country = country_object.name
#         except:
#             country_object = None
#             country = "USA"
#
#         # Calculate the tax rate based on the country object
#         if country_object:
#             tax_rate = country_object.tax_rate / 100
#         else:
#             tax_rate = 0
#
#         # Check if a cart item already exists for the given cart_id and course
#         cart = api_models.Cart.objects.filter(cart_id=cart_id, course=course).first()
#
#         if cart:
#             # If the cart item exists, update its details
#             cart.course = course
#             cart.user = user
#             cart.price = price
#             cart.tax_fee = Decimal(price) * Decimal(tax_rate)
#             cart.country = country
#             cart.cart_id = cart_id
#             cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
#             cart.save()
#
#             # Return a success response indicating the cart was updated
#             return Response({"message": "Cart updated Successfully"}, status=status.HTTP_200_OK)
#         else:
#             # If the cart item does not exist, create a new one
#             cart = api_models.Cart()
#             cart.course = course
#             cart.user = user
#             cart.price = price
#             cart.tax_fee = Decimal(price) * Decimal(tax_rate)
#             cart.country = country
#             cart.cart_id = cart_id
#             cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
#             cart.save()
#
#             # Return a success response indicating the cart was created
#             return Response({"message": "Cart created Successfully"}, status=status.HTTP_201_CREATED)
#
#
# class CartListAPIView(generics.ListAPIView):
#     serializer_class = api_serializer.CartSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         cart_id = self.kwargs['cart_id']
#         queryset = api_models.Cart.objects.filter(cart_id=cart_id)
#         return queryset
#
#
# class CartItemDeleteAPIView(generics.DestroyAPIView):
#     serializer_class = api_serializer.CartSerializer
#     permission_classes = [AllowAny]
#
#     def get_object(self):
#         cart_id = self.kwargs['cart_id']
#         item_id = self.kwargs['item_id']
#         return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()
#
#     def delete(self, request, *args, **kwargs):
#         cart_item = self.get_object()
#         if cart_item:
#             cart_item.delete()
#             return JsonResponse({'message': 'Item deleted'}, status=200)
#         else:
#             return JsonResponse({'message': 'Item not found'}, status=404)
#
#
# class CartStatsAPIView(generics.RetrieveAPIView):
#     """
#     Passing the cart_id by parameter, it gives back:
#     {
#       "price": 2000,
#       "tax": 420,
#       "total": 2420
#     }
#     """
#     serializer_class = api_serializer.CartSerializer
#     permission_classes = [AllowAny]
#     # This API by default will be expecting this field
#     lookup_field = 'cart_id'
#
#     @staticmethod
#     def calculate_price(cart_item):
#         return cart_item.price
#
#     @staticmethod
#     def calculate_tax(cart_item):
#         return cart_item.tax_fee
#
#     @staticmethod
#     def calculate_total(cart_item):
#         return cart_item.total
#
#     def get_queryset(self):
#         cart_id = self.kwargs['cart_id']
#         queryset = api_models.Cart.objects.filter(cart_id=cart_id)
#         return queryset
#
#     def get(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#
#         total_price = 0.00
#         total_tax = 0.00
#         total_total = 0.00
#
#         """
#         Accumulative sums for all the cart
#         Total + tax + Total
#         """
#         for cart_item in queryset:
#             total_price += float(self.calculate_price(cart_item))
#             total_tax += float(self.calculate_tax(cart_item))
#             total_total += round(float(self.calculate_total(cart_item)), 2)  #Round to 2 decimal places
#
#         data = {
#             "price": total_price,
#             "tax": total_tax,
#             "total": total_total
#         }
#
#         return Response(data, status.HTTP_200_OK)
#
#
# class CartOwnAPIView(generics.ListAPIView):
#     serializer_class = api_serializer.CartSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         cart_id = self.kwargs['cart_id']
#         return api_models.Cart.objects.filter(cart_id=cart_id)
#
#
# class EnrolledCoursesAPIView(generics.ListAPIView):
#     serializer_class = EnrolledCourseSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         user = get_user_from_request(self.request)
#         if user:
#             return EnrolledCourse.objects.filter(user=user)
#         else:
#             return EnrolledCourse.objects.none()
#
#
# class CreateOrderAPIView(generics.CreateAPIView):
#     """
#     The Payload fot this endpoint should be:
#     {
#         "full_name": "Juan Manuel Treviranus",
#         "email": "juantrevi70@gmail.com",
#         "country": "Argentina",
#         "cart_id": "548464",
#         "user_id": 1
#     }
#     """
#     serializer_class = api_serializer.CartOrderSerializer
#     permission_classes = [AllowAny]
#     queryset = api_models.CartOrder.objects.all()
#
#     def create(self, request, *args, **kwargs):
#         full_name = request.data['full_name']
#         email = request.data['email']
#         country = request.data['country']
#         cart_id = request.data['cart_id']
#         user_id = request.data['user_id']
#
#         if user_id != 0:
#             user = User.objects.get(id=user_id)
#         else:
#             user = None
#
#         cart_items = api_models.Cart.objects.filter(cart_id=cart_id)
#
#         total_price = Decimal(0.00)
#         total_tax = Decimal(0.00)
#         total_initial_total = Decimal(0.00)
#         total_total = Decimal(0.00)
#
#         order = api_models.CartOrder.objects.create(
#             full_name=full_name,
#             email=email,
#             country=country,
#             student=user
#         )
#
#         for c in cart_items:
#             api_models.CartOrderItem.objects.create(
#                 order=order,
#                 course=c.course,
#                 price=c.price,
#                 tax_fee=c.tax_fee,
#                 total=c.total,
#                 initial_total=c.total,
#                 teacher=c.course.teacher
#             )
#
#             total_price += Decimal(c.price)
#             total_tax += Decimal(c.tax_fee)
#             total_initial_total += Decimal(c.total)
#             total_total += Decimal(c.total)
#
#             order.teachers.add(c.course.teacher)
#
#         order.sub_total = total_price
#         order.tax_fee = total_tax
#         order.initial_total = total_initial_total
#         order.total = total_total
#         order.save()
#
#         return Response({"message": "Order created successfully", 'order_oid': order.oid}, status.HTTP_201_CREATED)
#
#
# class CheckOutAPIView(generics.RetrieveAPIView):
#     serializer_class = api_serializer.CartOrderSerializer
#     queryset = api_models.CartOrder.objects.all()
#     permission_classes = [AllowAny]
#     lookup_field = 'oid'
#
#
# class CouponApplyAPIView(generics.CreateAPIView):
#     """
#     Payload:
#     {
#       "order_oid": "473040",
#       "coupon_code": "CODE3"
#     }
#     """
#     serializer_class = api_serializer.CouponSerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         order_oid = request.data['order_oid']
#         coupon_code = request.data['coupon_code']
#
#         order = api_models.CartOrder.objects.get(oid=order_oid)
#         coupon = api_models.Coupon.objects.get(code=coupon_code)
#
#         """Check that the student can't make an
#         infinite number of uses for the coupon and
#         purchase course for 0.00"""
#         # Check i coupon exists
#         if coupon:
#             # If exists bring the items from the order
#             order_items = api_models.CartOrderItem.objects.filter(order=order, teacher=coupon.teacher)
#             # Loop the items and check if the coupon has been already applied
#             for i in order_items:
#                 # Check if the coupon does not exist in this specific cart order
#                 if not coupon in i.coupons.all():
#                     discount = i.total * coupon.discount / 100
#
#                     # Remove the discount from the total,
#                     # the price and adding the discount to the saved
#                     # (How much money the user saved)
#                     i.total -= discount
#                     i.price -= discount
#                     i.saved += discount
#                     i.applied_coupon = True
#
#                     # Add this coupon to the coupon lists
#                     i.coupons.add(coupon)
#
#                     # Saving the coupon to the order
#                     order.coupons.add(coupon)
#                     order.total -= discount
#                     order.sub_total -= discount
#                     order.saved += discount
#
#                     i.save()
#                     order.save()
#                     coupon.used_by.add(order.student)
#
#                     return Response({'message': 'Coupon found and activated', "icon": "success"},
#                                     status.HTTP_201_CREATED)
#                 else:
#                     return Response({'message': 'Coupon already applied', "icon": "warning"}, status.HTTP_200_OK)
#         else:
#             return Response({'message': 'Coupon not found', "icon": "error"}, status.HTTP_404_NOT_FOUND)
#
#
# class StripeCheckoutAPIView(generics.CreateAPIView):
#     serializer_class = api_serializer.CartOrderSerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         order_oid = self.kwargs['order_oid']
#         order = api_models.CartOrder.objects.filter(oid=order_oid).first()
#
#         if not order:
#             return Response({'message': 'Order Not Found'}, status=status.HTTP_404_NOT_FOUND)
#
#         try:
#             checkout_session = stripe.checkout.Session.create(
#                 customer_email=order.email,
#                 payment_method_types=['card'],
#                 line_items=[
#                     {
#                         'price_data': {
#                             'currency': 'eur',
#                             'product_data': {
#                                 'name': order.full_name,
#                             },
#                             'unit_amount': int(order.total * 100)
#                         },
#                         'quantity': 1
#                     }
#                 ],
#                 mode='payment',
#                 success_url=settings.FRONT_END_ROUTE_URL + '/payment-success/' + order.oid + '?session_id={CHECKOUT_SESSION_ID}',
#                 cancel_url=settings.FRONT_END_ROUTE_URL + '/payment-failed/'
#             )
#
#             order.stripe_session_id = checkout_session.id
#             order.save()
#
#             return redirect(checkout_session.url)
#         except stripe.error.StripeError as e:
#             return Response({'message': f'Something went wrong with the payment. Error: {str(e)}'},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#
# def get_access_token(client_id, secret_key):
#     """Function to get the paypal access
#     token from the frontend using client_id
#     and secret_key"""
#
#     token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
#     data = {'grant_type': 'client_credentials'}
#     auth = (client_id, secret_key)
#     response = requests.post(token_url, data=data, auth=auth)
#
#     if response.status_code == 200:
#         print('Access Token === ', response.json()['access_token'])
#         return response.json()['access_token']
#     else:
#         raise Exception(f'Failed to get access token from paypal {response.status_code}')
#
#
# class PaymentSuccessAPIView(generics.CreateAPIView):
#     serializer_class = api_serializer.CartOrderSerializer
#     queryset = api_models.CartOrder.objects.all()
#
#     def create(self, request, *args, **kwargs):
#         order_oid = request.data['order_oid']
#         session_id = request.data['session_id']
#         paypal_order_id = request.data['paypal_order_id']
#
#         order = api_models.CartOrder.objects.get(oid=order_oid)
#         order_items = api_models.CartOrderItem.objects.filter(order=order)
#
#         # Paypal payment success
#         if paypal_order_id != 'null':
#             paypal_api_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}'
#             headers = {
#                 'Content-type': 'application/json',
#                 'Authorization': f'Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}'
#             }
#             response = requests.get(paypal_api_url, headers=headers)
#             if response.status_code == 200:
#                 paypal_order_data = response.json()
#                 paypal_payment_status = paypal_order_data['status']
#                 if paypal_payment_status == 'COMPLETED':
#                     if order.payment_status == 'Processing':
#                         order.payment_status = "Paid"
#                         order.save()
#                         # Create a notification for the user
#                         api_models.Notification.objects.create(
#                             user=order.student,
#                             order=order,
#                             type="Course Enrollment Completed"
#                         )
#
#                         # Create a notification for ALL teachers in the order
#                         for i in order_items:
#                             api_models.Notification.objects.create(
#                                 teacher=i.teacher,
#                                 order=order,
#                                 order_item=i,
#                                 type="New Order"
#                             )
#
#                             api_models.EnrolledCourse.objects.create(
#                                 course=i.course,
#                                 user=order.student,
#                                 teacher=i.teacher,
#                                 order_item=i
#                             )
#
#                         return Response({'message': 'Payment Successful'})
#
#                     else:
#                         return Response({'message': 'Already Paid'})
#                 else:
#                     return Response({'message': 'Payment Failed'})
#             else:
#                 return Response({'message': 'PayPal Error Occurred'})
#
#         # Stripe Payment success
#         if session_id != 'null':
#             session = stripe.checkout.Session.retrieve(session_id)
#             if session.payment_status == 'paid':
#                 if order.payment_status == 'Processing':
#                     order.payment_status = "Paid"
#                     order.save()
#
#                     api_models.Notification.objects.create(
#                         user=order.student,
#                         order=order,
#                         type="Course Enrollment Completed"
#                     )
#
#                     # Create a notification for ALL teachers in the order
#                     for i in order_items:
#                         api_models.Notification.objects.create(
#                             teacher=i.teacher,
#                             order=order,
#                             order_item=i,
#                             type="New Order"
#                         )
#
#                         api_models.EnrolledCourse.objects.create(
#                             course=i.course,
#                             user=order.student,
#                             teacher=i.teacher,
#                             order_item=i
#                         )
#                     return Response({'message': 'Payment Successful'})
#                 else:
#                     return Response({'message': 'Already Paid'})
#             else:
#                 return Response({'message': 'Payment Failed'})
#
#
# class StudentSummaryAPIView(generics.ListAPIView):
#     serializer_class = api_serializer.StudentSummarySerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         user_id = self.kwargs['user_id']
#         user = User.objects.get(id=user_id)
#
#         total_courses = api_models.EnrolledCourse.objects.filter(user=user).count()
#         completed_lessons = api_models.CompletedLesson.objects.filter(user=user).count()
#         achieved_certificates = api_models.Certificate.objects.filter(user=user).count()
#
#         return [{
#             'total_courses': total_courses,
#             'completed_lessons': completed_lessons,
#             'achieved_certificates': achieved_certificates,
#         }]
#
#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)
#
#
# class StudentSummaryAPIViewNoIdPass(generics.ListAPIView):
#     serializer_class = api_serializer.StudentSummarySerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         user = get_user_from_request(self.request)
#         if not user:
#             return []
#
#         total_courses = api_models.EnrolledCourse.objects.filter(user=user).count()
#         completed_lessons = api_models.CompletedLesson.objects.filter(user=user).count()
#         achieved_certificates = api_models.Certificate.objects.filter(user=user).count()
#         enrolled_course_ids = list(
#             api_models.EnrolledCourse.objects.filter(user=user).values_list('course_id', flat=True))
#
#         return [{
#             'total_courses': total_courses,
#             'completed_lessons': completed_lessons,
#             'achieved_certificates': achieved_certificates,
#             'enrolled_course_ids': enrolled_course_ids,
#         }]
#
#     def list(self, request, *args, **kwargs):
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)
#
#
# class StudentCourseDetailAPIView(generics.RetrieveAPIView):
#     serializer_class = api_serializer.EnrolledCourseSerializer
#     permission_classes = [AllowAny]
#     lookup_field = 'enrollment_id'
#
#     def get_object(self):
#         user = get_user_from_request(self.request)
#         enrollment_id = self.kwargs['enrollment_id']
#
#         logging.debug(f"User: {user}")
#         logging.debug(f"Enrollment ID: {enrollment_id}")
#
#         if not user or not enrollment_id:
#             return []
#         else:
#             return api_models.EnrolledCourse.objects.get(user=user, enrollment_id=enrollment_id)
#
#
# class StudentCourseCompletedCreateAPIView(generics.CreateAPIView):
#     """
#     Payload:
#     {
#         "course_id": 4,
#         "variant_item_id": 767990
#     }
#     """
#
#     serializer_class = api_serializer.CompletedLessonSerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         user = get_user_from_request(request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         course_id = request.data['course_id']
#         variant_item_id = request.data['variant_item_id']
#
#         course = api_models.Course.objects.get(id=course_id)
#         variant_item = api_models.VariantItem.objects.get(variant_item_id=variant_item_id)
#
#         completed_lessons = api_models.CompletedLesson.objects.filter(user=user, course=course,
#                                                                       variant_item=variant_item).first()
#
#         if completed_lessons:
#             completed_lessons.delete()
#             return Response({'message': 'Lesson not completed'}, status=status.HTTP_201_CREATED)
#
#         else:
#             api_models.CompletedLesson.objects.create(user=user, course=course, variant_item=variant_item)
#             return Response({'message': 'Lesson completed'}, status=status.HTTP_201_CREATED)
#
#
# class StudentNoteCreateAPIView(generics.ListCreateAPIView):
#     """
#     Payload to be sent:
#     {
#       "enrollment_id": 691623,
#       "title": "A new Note",
#       "note":  "It is a long established
#                 fact that a reader will be distracted
#                 by the readable content of a page when
#                 looking at its layout. The point of
#                 using Lorem Ipsum is that it has a more-or
#                 -less normal distribution of letters,",
#     }
#     """
#
#     serializer_class = api_serializer.NoteSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#         enrollment_id = self.kwargs['enrollment_id']
#         enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
#
#         return api_models.Note.objects.filter(user=user, course=enrolled.course)
#
#     def create(self, request, *args, **kwargs):
#         user = get_user_from_request(request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         enrollment_id = request.data['enrollment_id']
#         title = request.data['title']
#         note = request.data['note']
#
#         enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
#
#         api_models.Note.objects.create(user=user, course=enrolled.course, note=note, title=title)
#
#         return Response({'message': 'Note created successfully'}, status.HTTP_201_CREATED)
#
#
# class StudentNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
#     """This endpoint lets update, get or delete a particular note:
#     PUT:
#     {
#      "enrollment_id": 691623,
#      "title": "A new Note PUT",
#      "course": 4,
#      "note":  "The note"
#     }
#     PATCH:
#     {
#      "enrollment_id": 691623,
#      "title": "A new Note PUT PATCH",
#      "course": 4,
#      "note":  "The note"
#     }
# """
#     serializer_class = api_serializer.NoteSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         return api_models.Note.objects.all()
#
#     def get_object(self):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         enrollment_id = self.kwargs['enrollment_id']
#         note_id = self.kwargs['note_id']
#
#         enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
#         note = api_models.Note.objects.get(user=user, course=enrolled.course, id=note_id)
#
#         return note
#
#
# class StudentRateCourseCreateAPIView(generics.CreateAPIView):
#     """
#     PAYLOAD
#     {
#     "course_id": 564235,
#     "rating": 4,
#     "review": "This is a great course!!",
#     }
#     OPTIONAL: "active": true
#     """
#     serializer_class = api_serializer.ReviewSerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         course_id = request.data['course_id']
#         rating = request.data['rating']
#         review = request.data['review']
#         # active = request.data['active']
#
#         course = api_models.Course.objects.get(course_id=course_id)
#
#         if api_models.Review.objects.filter(user=user, course=course).exists():
#             return Response({'message': 'You have already reviewed this course'})
#
#         # Add active=active
#         api_models.Review.objects.create(user=user, course=course, review=review, rating=rating)
#
#         return Response({"message": "Review created successfully"})
#
#
# class StudentRateCourseUpdateAPIView(generics.RetrieveUpdateAPIView):
#     serializer_class = api_serializer.ReviewSerializer
#     permission_classes = [AllowAny]
#
#     def get_object(self):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         review_id = self.kwargs['review_id']
#
#         return api_models.Review.objects.get(id=review_id, user=user)
#
#
# class StudentWishListListCreateAPIView(generics.ListCreateAPIView):
#     serializer_class = api_serializer.WishlistSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         return api_models.WishList.objects.filter(user=user)
#
#     def create(self, request, *args, **kwargs):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         course_id = request.data['course_id']
#         course = api_models.Course.objects.get(id=course_id)
#
#         wishlist = api_models.WishList.objects.filter(user=user, course=course).first()
#
#         if wishlist:
#             wishlist.delete()
#             return Response({'message': 'Deleted from wishlist'}, status=status.HTTP_200_OK)
#         else:
#             api_models.WishList.objects.create(
#                 user=user,
#                 course=course
#             )
#             return Response({'message': 'Added to wishlist'}, status=status.HTTP_201_CREATED)
#
#
# class QuestionAndAnswerListAPIView(generics.ListCreateAPIView):
#     serializer_class = api_serializer.QuestionAnswerSerializer
#     permission_classes = [AllowAny]
#
#     def get_queryset(self):
#         course_id = self.kwargs['course_id']
#         course = api_models.Course.objects.get(id=course_id)
#         return api_models.QuestionAnswer.objects.filter(course=course)
#
#     def create(self, request, *args, **kwargs):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         course_id = request.data['course_id']
#         title = request.data['title']
#         message = request.data['message']
#
#         course = api_models.Course.objects.get(id=course_id)
#
#         question = api_models.QuestionAnswer.objects.create(course=course, user=user, title=title)
#
#         api_models.QuestionAnswerMessage.objects.create(
#             course=course,
#             user=user,
#             message=message,
#             question=question
#         )
#
#         return Response({'message': 'Group conversation started'}, status=status.HTTP_201_CREATED)
#
#
# class QuestionAnswerMessageSendAPIView(generics.CreateAPIView):
#     """
#     PAYLOAD:
#     {
#     "course_id": 4,
#     "qa_id": 379665,
#     "message": "You have to run your server from the console"
#     }
#     """
#
#     serializer_class = api_serializer.QuestionAnswerMessageSerializer
#     permission_classes = [AllowAny]
#
#     def create(self, request, *args, **kwargs):
#         user = get_user_from_request(self.request)
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         course_id = request.data['course_id']
#         qa_id = request.data['qa_id']
#         message = request.data['message']
#
#         course = api_models.Course.objects.get(id=course_id)
#         question = api_models.QuestionAnswer.objects.get(qa_id=qa_id)
#
#         api_models.QuestionAnswerMessage.objects.create(course=course, user=user, message=message, question=question)
#
#         question_serializer = api_serializer.QuestionAnswerSerializer(question)
#         return Response({"message": "Message sent", "question": question_serializer.data})
#
#
#
