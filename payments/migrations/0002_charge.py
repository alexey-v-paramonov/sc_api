# Generated by Django 4.2.5 on 2024-02-19 20:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('service_type', models.PositiveSmallIntegerField(choices=[(0, 'Other services'), (1, 'Self hosted radio service'), (2, 'Hosted radio stream (traffic)'), (3, 'Hosted radio disk usage')], default=0, verbose_name='Service type')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Service description')),
                ('price', models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ('currency', models.PositiveSmallIntegerField(choices=[(0, '$'), (1, '₽'), (2, '€')], default=0, verbose_name='Currency')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]
