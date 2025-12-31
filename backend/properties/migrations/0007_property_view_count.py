from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0006_property_availability"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="view_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
