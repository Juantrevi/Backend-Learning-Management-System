import random
import string

from django.db import models
from userauths.models import User, Profile
from django.utils.text import slugify
from .constants import CourseConstants
from shortuuid.django_fields import ShortUUIDField
from django.utils import timezone


class Teacher(models.Model):
    # One User model should be associated with one teacher
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="course-file", blank=True, null=True, default="default.jpg")
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=200, null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    x = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    country = models.CharField(null=True, blank=True, max_length=100)

    def __str__(self):
        return self.full_name

    def students(self):
        return CartOrderItem.obejct.filter(teacher=self)

    def courses(self):
        return Course.objects.filter(teacher=self)

    def review(self):
        return Course.objects.filter(teacher=self).count


class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to="course-file", default="category.jpg", null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Category"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def course_count(self):
        return Course.objects.filter(category=self).count()

    def save(self, *args, **kwargs):
        if not self.slug:
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            self.slug = slugify(f"{self.title}-{random_string}")
        super(Category, self).save()


class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to="course-file", blank=True, null=True)
    image = models.FileField(upload_to="course-file", blank=True, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    language = models.CharField(choices=CourseConstants.LANGUAGES, default='English', max_length=100)
    level = models.CharField(choices=CourseConstants.LEVEL, default='Beginner', max_length=100)
    platform_status = models.CharField(choices=CourseConstants.PLATFORM_STATUS, default='Published', max_length=100)
    teacher_course_status = models.CharField(choices=CourseConstants.TEACHER_STATUS, default='Published', max_length=100)
    featured = models.BooleanField(default=False)
    course_id = ShortUUIDField(unique=True, length=6, max_length=20, alphabet="1234567890")
    slug = models.SlugField(unique=True, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            self.slug = slugify(f"{self.title}-{random_string}")
        super(Course, self).save()
