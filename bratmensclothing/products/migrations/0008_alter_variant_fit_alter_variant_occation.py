# Generated by Django 5.1.2 on 2024-10-19 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_remove_variant_ocation_variant_occation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variant',
            name='fit',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='variant',
            name='occation',
            field=models.CharField(max_length=30),
        ),
    ]
