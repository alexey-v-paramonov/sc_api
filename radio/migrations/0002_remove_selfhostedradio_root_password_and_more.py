# Generated by Django 4.2.5 on 2023-10-20 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='selfhostedradio',
            name='root_password',
        ),
        migrations.AddField(
            model_name='selfhostedradio',
            name='ssh_port',
            field=models.PositiveIntegerField(default=22, verbose_name='SSH port'),
        ),
        migrations.AddField(
            model_name='selfhostedradio',
            name='ssh_username',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='SSH user username'),
        ),
    ]