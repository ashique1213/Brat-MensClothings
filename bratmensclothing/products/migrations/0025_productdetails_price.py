# Generated by Django 5.1.2 on 2024-11-09 04:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0024_alter_productdetails_image2_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productdetails',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
