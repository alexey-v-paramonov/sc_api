# Generated by Django 4.2.5 on 2023-09-08 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_user_username_alter_user_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='balance',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='currency',
            field=models.PositiveSmallIntegerField(choices=[(0, '$'), (1, '₽')], default=0, verbose_name='Currency'),
        ),
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.PositiveSmallIntegerField(choices=[(0, 'English'), (1, 'Russian')], default=0, verbose_name='Language'),
        ),
    ]