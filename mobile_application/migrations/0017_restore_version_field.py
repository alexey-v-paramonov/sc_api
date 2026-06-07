from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_application', '0016_alter_androidapplication_version_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='androidapplication',
            old_name='version',
            new_name='version_code',
        ),
        migrations.RenameField(
            model_name='iosapplication',
            old_name='version',
            new_name='version_code',
        ),
        migrations.AddField(
            model_name='androidapplication',
            name='version',
            field=models.PositiveIntegerField(blank=True, default=1),
        ),
        migrations.AddField(
            model_name='iosapplication',
            name='version',
            field=models.PositiveIntegerField(blank=True, default=1),
        ),
    ]
