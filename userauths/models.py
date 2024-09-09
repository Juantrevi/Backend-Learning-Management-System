from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save


# Custom user model extending AbstractUser
class User(AbstractUser):
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    # One-time password (OTP) field, unique and with a maximum length of 100 characters
    otp = models.CharField(unique=True, max_length=100)

    # Use email as the unique identifier for authentication instead of username
    USERNAME_FIELD = 'email'
    # Required fields for creating a user
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        # String representation of the user, returns the email
        return self.email

    # Override the save method to set default values for full_name and username
    def save(self, *args, **kwargs):
        # Split the email to get the part before the "@" symbol
        email_username, full_name = self.email.split("@")
        # If full_name is empty or None, set it to the part before the "@" symbol
        if self.full_name == "" or self.full_name is None:
            self.full_name = email_username
        # If username is empty or None, set it to the part before the "@" symbol
        if self.username == "" or self.username is None:
            self.username = email_username
        # Call the parent class's save method
        super(User, self).save(*args, **kwargs)


# Profile model linked to the User model
class Profile(models.Model):
    # One-to-one relationship with the User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # File field for the profile image, with a default image and allowing null/blank values
    image = models.FileField(upload_to="user_folder", default="default-user.jpg", null=True, blank=True)
    full_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        # String representation of the profile, returns the full name or the user's full name
        if self.full_name:
            return str(self.full_name)
        else:
            return str(self.user.full_name)

    # Override the save method to set default values for full_name
    def save(self, *args, **kwargs):
        # If full_name is empty or None, set it to the user's username
        if self.full_name == "" or self.full_name is None:
            self.full_name = self.user.username
        # Call the parent class's save method
        super(Profile, self).save(*args, **kwargs)


# User Model: Customizes the default user model to use email
#     as the unique identifier and sets default values for username
#     and full_name if they are not provided.

# Profile Model: Extends the user model with
#     additional fields like image, country, and
#     about, and sets default values for full_name if not provided.


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
