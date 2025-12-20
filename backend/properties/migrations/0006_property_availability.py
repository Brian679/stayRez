from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0005_property_max_occupancy"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="is_available",
            field=models.BooleanField(default=True),
        ),
    ]
