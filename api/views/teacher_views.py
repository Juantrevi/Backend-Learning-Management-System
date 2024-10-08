from django.db.models.functions import ExtractMonth
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny

from api import models as api_models
from api.utils import generate_random_otp, get_user_from_request
from userauths.models import User, Profile
from api import serializer as api_serializer
from datetime import datetime, timedelta
from django.db import models


class TeacherSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializer.TeacherSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        one_month_ago = datetime.today() - timedelta(days=28)

        total_courses = api_models.Course.objects.filter(teacher=teacher).count()

        total_revenue = \
            api_models.CartOrderItem.objects.filter(teacher=teacher, order__payment_status='Paid').aggregate(
                total_revenue=models.Sum('price'))['total_revenue'] or 0

        monthly_revenue = api_models.CartOrderItem.objects.filter(teacher=teacher, order__payment_status='Paid',
                                                                  date__gte=one_month_ago).aggregate(
            total_revenue=models.Sum('price'))['total_revenue'] or 0

        enrolled_course = api_models.EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        total_students = []

        for course in enrolled_course:
            if course.user_id not in unique_student_ids:
                user = User.objects.get(id=course.user_id)
                student = {
                    'full_name': user.profile.full_name,
                    'image': user.profile.image.url,
                    'country': user.profile.country,
                    'date': user.profile.date,
                }
                total_students.append(student)
                unique_student_ids.add(course.user_id)
        return [{
            'total_courses': total_courses,
            'total_students': len(total_students),
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
        }]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TeacherCourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        return api_models.Course.objects.filter(teacher=teacher)


class TeacherReviewListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        return api_models.Review.objects.filter(course__teacher=teacher)


class TeacherReviewDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializer.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user = get_user_from_request(self.request)
        review_id = self.kwargs['review_id']
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        return api_models.Review.objects.get(course__teacher=teacher, id=review_id)


class TeacherStudentsListAPIView(viewsets.ViewSet):

    def list(self, request):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        enrolled_course = api_models.EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        total_students = []

        for course in enrolled_course:
            if course.user_id not in unique_student_ids:
                user = User.objects.get(id=course.user_id)
                student = {
                    'full_name': user.profile.full_name,
                    'image': user.profile.image.url,
                    'country': user.profile.country,
                    'date': user.profile.date,
                }
                total_students.append(student)
                unique_student_ids.add(course.user_id)

        return Response(total_students)


@api_view({'GET'})
def TeacherAllMonthsEarningAPIView(request, teacher_id):
    teacher = api_models.Teacher.objects.get(id=teacher_id)
    monthly_earning_tracker = (
        api_models.CartOrderItem.objects
        .filter(teacher=teacher, order__payment_status='Paid')
        .annotate(
            month=ExtractMonth('date')
        )
        .values('months')
        .annotate(
            total_earning = models.Sum('price')
        )
        .order_by('month')
    )

    return Response(monthly_earning_tracker)


class TeacherBestSellingCourseAPIView(viewsets.ViewSet):

    def list(self, request):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        courses_with_total_price = []
        courses = api_models.Course.objects.filter(teacher=teacher)

        for course in courses:
            revenue = course.enrolledcourse_set.aggregate(total_price=models.Sum('order_item__price'))['total_price'] or 0
            sales = course.enrolledcourse_set.count()

            courses_with_total_price.append({
                'course_image': course.image.url,
                'course_title': course.title,
                'revenue': revenue,
                'sales': sales,
            })
        return Response(courses_with_total_price)


class TeacherCourseOrdersListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CartOrderItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        return api_models.CartOrderItem.objects.filter(teacher=teacher)


class TeacherQuestionAnswerListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = get_user_from_request(self.request)
        if user:
            teacher = api_models.Teacher.objects.filter(user=user).first()
            if not teacher:
                raise ValueError('No teacher found')
        else:
            raise ValueError('No user found')

        return api_models.QuestionAnswer.objects.filter(course__teacher=teacher)


