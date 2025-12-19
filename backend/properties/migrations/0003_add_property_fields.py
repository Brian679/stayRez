from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0002_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='price_per_month',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='amenities',
            field=models.TextField(blank=True, help_text='Comma-separated amenities (e.g., WiFi,Parking,Kitchen)'),
        ),
        migrations.AddField(
            model_name='property',
            name='distance_to_campus_km',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='square_meters',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='bedrooms',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='bathrooms',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='rating_stars',
            field=models.IntegerField(blank=True, help_text='1-5 stars', null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='all_inclusive',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='property',
            name='shop_category',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
