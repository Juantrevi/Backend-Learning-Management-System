# Generated by Django 5.0 on 2024-09-14 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauths', '0005_alter_profile_full_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='full_name',
            field=models.CharField(max_length=100),
        ),
    ]
