# Generated by Django 5.1.2 on 2024-11-10 19:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0028_remove_variantsize_price'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='variantsize',
            options={'ordering': ['size']},
        ),
    ]
