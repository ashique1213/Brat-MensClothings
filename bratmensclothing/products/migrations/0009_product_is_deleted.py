# Generated by Django 5.1.2 on 2024-10-20 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_alter_variant_fit_alter_variant_occation'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
