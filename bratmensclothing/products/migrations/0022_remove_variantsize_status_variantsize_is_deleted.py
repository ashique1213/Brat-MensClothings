# Generated by Django 5.1.2 on 2024-11-02 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_alter_variantsize_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='variantsize',
            name='status',
        ),
        migrations.AddField(
            model_name='variantsize',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
