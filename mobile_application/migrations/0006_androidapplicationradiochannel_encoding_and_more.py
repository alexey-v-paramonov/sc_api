# Generated by Django 4.2.5 on 2024-07-02 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mobile_application", "0005_iosapplication_package_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="androidapplicationradiochannel",
            name="encoding",
            field=models.CharField(
                blank=True,
                default="utf8",
                max_length=10,
                verbose_name="Stream metadata character encoding, mostly utf8/cp1251",
            ),
        ),
        migrations.AddField(
            model_name="iosapplicationradiochannel",
            name="encoding",
            field=models.CharField(
                blank=True,
                default="utf8",
                max_length=10,
                verbose_name="Stream metadata character encoding, mostly utf8/cp1251",
            ),
        ),
    ]
