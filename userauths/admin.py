from django.contrib import admin
from userauths.models import User, Profile


# Custom admin class for the Profile model in the admin dashboard
class ProfileAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view dashboard
    list_display = ['user', 'full_name', 'date']


# Register the User model with the admin site
admin.site.register(User)
# Register the Profile model with the admin site using the custom ProfileAdmin class
admin.site.register(Profile, ProfileAdmin)

