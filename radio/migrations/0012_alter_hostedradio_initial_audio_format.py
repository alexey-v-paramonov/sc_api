# Generated by Django 4.2.5 on 2024-03-16 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radio', '0011_alter_selfhostedradio_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hostedradio',
            name='initial_audio_format',
            field=models.CharField(blank=True, choices=[('mp3', 'Mp3'), ('aac', 'AAC'), ('flac', 'FLAC')], max_length=10, null=True, verbose_name='Audio format'),
        ),
    ]