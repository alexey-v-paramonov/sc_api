# Generated by Django 4.2.5 on 2024-03-29 06:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0012_alter_hostedradio_initial_audio_format'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hostedradio',
            name='login',
            field=models.CharField(blank=True, max_length=32, null=True, validators=[django.core.validators.RegexValidator('^[a-zA-Z_]([a-zA-Z0-9_-]{0,31}|[a-zA-Z0-9_-]{0,30}\\$)$')], verbose_name='Hosting login name'),
        ),
    ]
