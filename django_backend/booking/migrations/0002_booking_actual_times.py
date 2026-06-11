from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="actual_check_in_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="实际签到时间"),
        ),
        migrations.AddField(
            model_name="booking",
            name="actual_check_out_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="实际签退时间"),
        ),
    ]
