from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from decimal import Decimal
from api import models as api_models
from api import serializer as api_serializer
from api.utils import User


class CartAPIView(generics.CreateAPIView):
    queryset = api_models.Cart.objects.all()
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']
        user_id = request.data['user_id']
        price = request.data['price']
        country_name = request.data['country_name']
        cart_id = request.data['cart_id']
        course = api_models.Course.objects.filter(id=course_id).first()
        user = User.objects.filter(id=user_id).first() if user_id != "undefined" else None
        country_object = api_models.Country.objects.filter(name=country_name).first()
        country = country_object.name if country_object else "USA"
        tax_rate = country_object.tax_rate / 100 if country_object else 0
        cart = api_models.Cart.objects.filter(cart_id=cart_id, course=course).first()
        if cart:
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()
            return Response({"message": "Cart updated Successfully"}, status=status.HTTP_200_OK)
        else:
            cart = api_models.Cart()
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id
            cart.total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.save()
            return Response({"message": "Cart created Successfully"}, status=status.HTTP_201_CREATED)


class CreateOrderAPIView(generics.CreateAPIView):
    """
    The Payload for this endpoint should be:
    {
        "full_name": "Juan Manuel Treviranus",
        "email": "juantrevi70@gmail.com",
        "country": "Argentina",
        "cart_id": "548464",
        "user_id": 1
    }
    """
    serializer_class = api_serializer.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        full_name = request.data['full_name']
        email = request.data['email']
        country = request.data['country']
        cart_id = request.data['cart_id']
        user_id = request.data['user_id']

        if user_id != 0:
            user = User.objects.get(id=user_id)
        else:
            user = None

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


class CheckOutAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CartOrderSerializer
    queryset = api_models.CartOrder.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'oid'


class CouponApplyAPIView(generics.CreateAPIView):
    """
    Payload:
    {
      "order_oid": "473040",
      "coupon_code": "CODE3"
    }
    """
    serializer_class = api_serializer.CouponSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_oid = request.data['order_oid']
        coupon_code = request.data['coupon_code']

        order = api_models.CartOrder.objects.get(oid=order_oid)
        coupon = api_models.Coupon.objects.get(code=coupon_code)

        """Check that the student can't make an 
        infinite number of uses for the coupon and 
        purchase course for 0.00"""
        # Check i coupon exists
        if coupon:
            # If exists bring the items from the order
            order_items = api_models.CartOrderItem.objects.filter(order=order, teacher=coupon.teacher)
            # Loop the items and check if the coupon has been already applied
            for i in order_items:
                # Check if the coupon does not exist in this specific cart order
                if not coupon in i.coupons.all():
                    discount = i.total * coupon.discount / 100

                    # Remove the discount from the total,
                    # the price and adding the discount to the saved
                    # (How much money the user saved)
                    i.total -= discount
                    i.price -= discount
                    i.saved += discount
                    i.applied_coupon = True

                    # Add this coupon to the coupon lists
                    i.coupons.add(coupon)

                    # Saving the coupon to the order
                    order.coupons.add(coupon)
                    order.total -= discount
                    order.sub_total -= discount
                    order.saved += discount

                    i.save()
                    order.save()
                    coupon.used_by.add(order.student)

                    return Response({'message': 'Coupon found and activated', "icon": "success"},
                                    status.HTTP_201_CREATED)
                else:
                    return Response({'message': 'Coupon already applied', "icon": "warning"}, status.HTTP_200_OK)
        else:
            return Response({'message': 'Coupon not found', "icon": "error"}, status.HTTP_404_NOT_FOUND)


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
        item_id = self.kwargs['item_id']
        return api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()

    def delete(self, request, *args, **kwargs):
        cart_item = self.get_object()
        if cart_item:
            cart_item.delete()
            return JsonResponse({'message': 'Item deleted'}, status=200)
        else:
            return JsonResponse({'message': 'Item not found'}, status=404)


class CartStatsAPIView(generics.RetrieveAPIView):
    """
    Passing the cart_id by parameter, it gives back:
    {
      "price": 2000,
      "tax": 420,
      "total": 2420
    }
    """
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
            total_total += round(float(self.calculate_total(cart_item)), 2)  #Round to 2 decimal places

        data = {
            "price": total_price,
            "tax": total_tax,
            "total": total_total
        }

        return Response(data, status.HTTP_200_OK)


class CartOwnAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        return api_models.Cart.objects.filter(cart_id=cart_id)