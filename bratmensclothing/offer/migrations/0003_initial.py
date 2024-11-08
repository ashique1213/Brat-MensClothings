# Generated by Django 5.1.2 on 2024-11-08 10:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('offer', '0002_remove_product_offers_product_id_delete_brand_offers_and_more'),
        ('products', '0024_alter_productdetails_image2_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand_Offers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('offer_price', models.IntegerField()),
                ('status', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('offer_name', models.CharField(blank=True, null=True)),
                ('strted_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(auto_now_add=True)),
                ('offer_details', models.TextField(blank=True, null=True)),
                ('brand_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.brand')),
            ],
        ),
        migrations.CreateModel(
            name='Product_Offers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('offer_price', models.IntegerField()),
                ('status', models.BooleanField(default=True)),
                ('offer_name', models.CharField(blank=True, null=True)),
                ('offer_details', models.TextField(blank=True, null=True)),
                ('strted_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.variantsize')),
            ],
        ),
    ]
