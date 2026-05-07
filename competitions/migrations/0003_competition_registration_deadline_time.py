from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("competitions", "0002_remove_result_athlete_remove_result_competition_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="competition",
            name="registration_deadline_time",
            field=models.CharField(default="23:59", max_length=5, verbose_name="Время закрытия заявок"),
        ),
    ]
