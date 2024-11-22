# Generated by Django 5.1.2 on 2024-11-11 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0004_alter_transaction_details'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=30),
        ),
    ]
