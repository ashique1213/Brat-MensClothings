# Generated by Django 5.1.2 on 2024-10-18 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('category_id', models.AutoField(primary_key=True, serialize=False)),
                ('brand_name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('Tshirt', 'T-shirt'), ('Shirt', 'Shirt'), ('Jeans', 'Jeans'), ('Pants', 'Pants')], max_length=50)),
                ('category_unit', models.CharField(max_length=50)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
