# Generated by Django 5.1.2 on 2024-11-19 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer', '0007_rename_brand_id_brand_offers_brand_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand_offers',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='brand_offers',
            name='started_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product_offers',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product_offers',
            name='started_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
