# Generated by Django 4.2.5 on 2024-02-21 18:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0004_portregistry'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='portregistry',
            unique_together={('radio', 'port')},
        ),
    ]