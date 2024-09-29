import requests
import stripe
from django.shortcuts import redirect
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from api import models as api_models
from api import serializer as api_serializer
from decimal import Decimal

from api.utils import User
from backend import settings
from environs import Env

env = Env()
env.read_env()

stripe.api_key = settings.STRIPE_SECRET_KEY
PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID


class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        full_name = request.data['full_name']
        email = request.data['email']
        country = request.data['country']
        cart_id = request.data['cart_id']
        user_id = request.data['user_id']
        user = User.objects.get(id=user_id) if user_id != 0 else None
        cart_items = api_models.Cart.objects.filter(cart_id=cart_id)
        total_price = Decimal(0.00)
        total_tax = Decimal(0.00)
        total_initial_total = Decimal(0.00)
        total_total = Decimal(0.00)
        order = api_models.CartOrder.objects.create(
            full_name=full_name,
            email=email,
            country=country,
            student=user
        )
        for c in cart_items:
            api_models.CartOrderItem.objects.create(
                order=order,
                course=c.course,
                price=c.price,
                tax_fee=c.tax_fee,
                total=c.total,
                initial_total=c.total,
                teacher=c.course.teacher
            )
            total_price += Decimal(c.price)
            total_tax += Decimal(c.tax_fee)
            total_initial_total += Decimal(c.total)
            total_total += Decimal(c.total)
            order.teachers.add(c.course.teacher)
        order.sub_total = total_price
        order.tax_fee = total_tax
        order.initial_total = total_initial_total
        order.total = total_total
        order.save()
        return Response({"message": "Order created successfully", 'order_oid': order.oid}, status.HTTP_201_CREATED)


class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_oid = self.kwargs['order_oid']
        order = api_models.CartOrder.objects.filter(oid=order_oid).first()

        if not order:
            return Response({'message': 'Order Not Found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=order.email,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': order.full_name,
                            },
                            'unit_amount': int(order.total * 100)
                        },
                        'quantity': 1
                    }
                ],
                mode='payment',
                success_url=settings.FRONT_END_ROUTE_URL + '/payment-success/' + order.oid + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.FRONT_END_ROUTE_URL + '/payment-failed/'
            )

            order.stripe_session_id = checkout_session.id
            order.save()

            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response({'message': f'Something went wrong with the payment. Error: {str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST)


def get_access_token(client_id, secret_key):
    """Function to get the paypal access
    token from the frontend using client_id
    and secret_key"""

    token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
    data = {'grant_type': 'client_credentials'}
    auth = (client_id, secret_key)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print('Access Token === ', response.json()['access_token'])
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to get access token from paypal {response.status_code}')


class PaymentSuccessAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        order_oid = request.data['order_oid']
        session_id = request.data['session_id']
        paypal_order_id = request.data['paypal_order_id']

        order = api_models.CartOrder.objects.get(oid=order_oid)
        order_items = api_models.CartOrderItem.objects.filter(order=order)

        # Paypal payment success
        if paypal_order_id != 'null':
            paypal_api_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}'
            headers = {
                'Content-type': 'application/json',
                'Authorization': f'Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}'
            }
            response = requests.get(paypal_api_url, headers=headers)
            if response.status_code == 200:
                paypal_order_data = response.json()
                paypal_payment_status = paypal_order_data['status']
                if paypal_payment_status == 'COMPLETED':
                    if order.payment_status == 'Processing':
                        order.payment_status = "Paid"
                        order.save()
                        # Create a notification for the user
                        api_models.Notification.objects.create(
                            user=order.student,
                            order=order,
                            type="Course Enrollment Completed"
                        )

                        # Create a notification for ALL teachers in the order
                        for i in order_items:
                            api_models.Notification.objects.create(
                                teacher=i.teacher,
                                order=order,
                                order_item=i,
                                type="New Order"
                            )

                            api_models.EnrolledCourse.objects.create(
                                course=i.course,
                                user=order.student,
                                teacher=i.teacher,
                                order_item=i
                            )

                        return Response({'message': 'Payment Successful'})

                    else:
                        return Response({'message': 'Already Paid'})
                else:
                    return Response({'message': 'Payment Failed'})
            else:
                return Response({'message': 'PayPal Error Occurred'})

        # Stripe Payment success
        if session_id != 'null':
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                if order.payment_status == 'Processing':
                    order.payment_status = "Paid"
                    order.save()

                    api_models.Notification.objects.create(
                        user=order.student,
                        order=order,
                        type="Course Enrollment Completed"
                    )

                    # Create a notification for ALL teachers in the order
                    for i in order_items:
                        api_models.Notification.objects.create(
                            teacher=i.teacher,
                            order=order,
                            order_item=i,
                            type="New Order"
                        )

                        api_models.EnrolledCourse.objects.create(
                            course=i.course,
                            user=order.student,
                            teacher=i.teacher,
                            order_item=i
                        )
                    return Response({'message': 'Payment Successful'})
                else:
                    return Response({'message': 'Already Paid'})
            else:
                return Response({'message': 'Payment Failed'})
