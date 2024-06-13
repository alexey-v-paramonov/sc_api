# Generated by Django 4.2.5 on 2024-06-13 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("radio", "0015_hostedradio_custom_price"),
    ]

    operations = [
        migrations.AddField(
            model_name="hostedradio",
            name="branded_url",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="hostedradio",
            name="branded_url_status",
            field=models.PositiveIntegerField(
                choices=[
                    (0, "Inactive"),
                    (1, "Working"),
                    (2, "Active"),
                    (3, "Error setting up DNS"),
                    (4, "Error configuring Apache"),
                    (5, "Error setting up SSL certificate"),
                    (6, "Error configuring Nginx"),
                    (7, "Error in broadcaster interface"),
                    (8, "Other error"),
                ],
                default=0,
            ),
        ),
    ]
