# Generated by Django 5.1.2 on 2024-11-05 12:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_remove_variantsize_status_variantsize_is_deleted'),
        ('wishlist', '0001_initial'), 
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlist',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.variantsize'),
        ),
    ]
