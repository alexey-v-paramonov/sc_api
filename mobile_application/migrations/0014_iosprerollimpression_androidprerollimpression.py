# Generated by Django 4.2.5 on 2025-06-17 17:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "mobile_application",
            "0013_androidapplicationradio_prerolls_update_ts_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="iOSPrerollImpression",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("ip", models.GenericIPAddressField(verbose_name="IP address")),
                (
                    "preroll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="impressions",
                        to="mobile_application.iosradiopreroll",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AndroidPrerollImpression",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("ip", models.GenericIPAddressField(verbose_name="IP address")),
                (
                    "preroll",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="impressions",
                        to="mobile_application.androidradiopreroll",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
