from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incident', '0002_user_login_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incidentreport',
            name='photo',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_photo',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]