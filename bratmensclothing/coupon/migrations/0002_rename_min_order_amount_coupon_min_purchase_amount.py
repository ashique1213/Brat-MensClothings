# Generated by Django 5.1.2 on 2024-11-05 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coupon',
            old_name='min_order_amount',
            new_name='min_purchase_amount',
        ),
    ]
