# Generated by Django 5.1.2 on 2024-10-18 05:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('brand_id', models.AutoField(primary_key=True, serialize=False)),
                ('brandname', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='category',
            name='brand_name',
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('product_id', models.AutoField(primary_key=True, serialize=False)),
                ('product_name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.brand')),
                ('categories', models.ManyToManyField(related_name='products', to='products.category')),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('variant_id', models.AutoField(primary_key=True, serialize=False)),
                ('image1', models.ImageField(upload_to='products/')),
                ('image2', models.ImageField(upload_to='products/')),
                ('image3', models.ImageField(upload_to='products/')),
                ('image4', models.ImageField(upload_to='products/')),
                ('image5', models.ImageField(upload_to='products/')),
                ('size', models.CharField()),
                ('color', models.CharField(max_length=30)),
                ('ocation', models.CharField(max_length=30)),
                ('fit', models.CharField(max_length=30)),
                ('qty', models.IntegerField()),
                ('price', models.IntegerField(blank=True, null=True)),
                ('status', models.BooleanField(default=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
        ),
    ]
