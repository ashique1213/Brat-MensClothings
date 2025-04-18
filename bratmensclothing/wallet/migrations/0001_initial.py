# Generated by Django 5.1.2 on 2024-11-10 14:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('wallet_id', models.AutoField(primary_key=True, serialize=False)),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('transaction_id', models.AutoField(primary_key=True, serialize=False)),
                ('Dtails', models.CharField(max_length=50)),
                ('amount', models.IntegerField(blank=True, null=True)),
                ('transaction_type', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('wallet_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wallet.wallet')),
            ],
        ),
    ]
