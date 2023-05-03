# Generated by Django 4.1.7 on 2023-04-21 10:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_remove_cart_ordered_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='ordered_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
