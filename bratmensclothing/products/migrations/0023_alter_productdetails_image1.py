# Generated by Django 5.1.2 on 2024-11-08 05:09

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_remove_variantsize_status_variantsize_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productdetails',
            name='image1',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='image'),
        ),
    ]
