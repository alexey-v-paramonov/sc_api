# Generated by Django 4.2.5 on 2024-02-19 06:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='hostedradioservice',
            unique_together={('channel_id', 'radio')},
        ),
    ]