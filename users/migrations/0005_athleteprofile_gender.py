from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_secretaryprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="athleteprofile",
            name="gender",
            field=models.CharField(
                choices=[("M", "Мужчина"), ("F", "Женщина")],
                default="M",
                max_length=1,
                verbose_name="Пол",
            ),
        ),
    ]
