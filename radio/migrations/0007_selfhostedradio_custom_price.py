# Generated by Django 4.2.5 on 2024-02-18 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0006_hostedradioservice'),
    ]

    operations = [
        migrations.AddField(
            model_name='selfhostedradio',
            name='custom_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
