# Generated by Django 5.1.2 on 2024-11-09 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_alter_order_coupon_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='coupon_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, null=True),
        ),
    ]