# from django.contrib import admin
# from api import models
#
#
# admin.site.register(models.Teacher)
# admin.site.register(models.Category)
# admin.site.register(models.Course)
# admin.site.register(models.Variant)
# admin.site.register(models.VariantItem)
# admin.site.register(models.QuestionAnswer)
# admin.site.register(models.QuestionAnswerMessage)
# admin.site.register(models.Cart)
# admin.site.register(models.CartOrder)
# admin.site.register(models.CartOrderItem)
# admin.site.register(models.Certificate)
# admin.site.register(models.CompletedLesson)
# admin.site.register(models.EnrolledCourse)
# admin.site.register(models.Note)
# admin.site.register(models.Review)
# admin.site.register(models.Notification)
# admin.site.register(models.Coupon)
# admin.site.register(models.WishList)
# admin.site.register(models.Country)
# # Register your models here.

# api/admin.py
from django.contrib import admin
from django.apps import apps

app = apps.get_app_config('api')

for model_name, model in app.models.items():
    admin.site.register(model)
