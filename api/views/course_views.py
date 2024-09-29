from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Avg
from api import models as api_models
from api import serializer as api_serializer


class CourseListAPIView(generics.ListAPIView):
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]


class BestCoursesListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return api_models.Course.objects.filter(
            platform_status="Published",
            teacher_course_status="Published"
        ).annotate(
            avg_rating=Avg('review__rating')
        ).order_by('-avg_rating')[:4]


class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        slug = self.kwargs['slug']
        return api_models.Course.objects.get(slug=slug, platform_status="Published", teacher_course_status="Published")


class SearchCourseAPIView(generics.ListAPIView):
    serializer_class = api_serializer.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get('query')
        return api_models.Course.objects.filter(
            title__icontains=query,
            platform_status="Published",
            teacher_course_status="Published"
        )


class CategoryListAPIView(generics.ListAPIView):
    queryset = api_models.Category.objects.filter(active=True)
    serializer_class = api_serializer.CategorySerializer
    # TODO: Change the permission
    permission_classes = [AllowAny]

