# Generated by Django 5.1.2 on 2025-03-22 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0007_order_total_offer_discount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, default='0', max_length=255, null=True),
        ),
    ]
