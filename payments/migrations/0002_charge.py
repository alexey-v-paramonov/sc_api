# Generated by Django 4.2.5 on 2024-02-19 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
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
                ('price', models.DecimalField(decimal_places=3, default=0, max_digits=6)),
            ],
        ),
    ]
