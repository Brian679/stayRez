from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, blank=True)),
                ("age", models.CharField(max_length=20, blank=True)),
                ("gender", models.CharField(max_length=20, blank=True)),
                ("occupation", models.CharField(max_length=30, blank=True)),
                ("occupation_other", models.CharField(max_length=100, blank=True)),
                ("city", models.CharField(max_length=30, blank=True)),
                ("has_internet", models.CharField(max_length=5, blank=True)),
                ("online_search_freq", models.CharField(max_length=20, blank=True)),
                ("current_methods", models.CharField(max_length=200, blank=True)),
                ("current_methods_rating", models.CharField(max_length=20, blank=True)),
                ("challenges", models.CharField(max_length=200, blank=True)),
                ("easy_to_use", models.IntegerField(null=True, blank=True)),
                ("user_friendly", models.IntegerField(null=True, blank=True)),
                ("quick_response", models.IntegerField(null=True, blank=True)),
                ("easy_search", models.IntegerField(null=True, blank=True)),
                ("access_anytime", models.IntegerField(null=True, blank=True)),
                ("works_on_device", models.IntegerField(null=True, blank=True)),
                ("reasonable_internet", models.IntegerField(null=True, blank=True)),
                ("map_helps", models.IntegerField(null=True, blank=True)),
                ("view_distance", models.IntegerField(null=True, blank=True)),
                ("spatial_search", models.IntegerField(null=True, blank=True)),
                ("visualization_clear", models.IntegerField(null=True, blank=True)),
                ("info_accurate", models.IntegerField(null=True, blank=True)),
                ("trustworthy", models.IntegerField(null=True, blank=True)),
                ("up_to_date", models.IntegerField(null=True, blank=True)),
                ("satisfied", models.IntegerField(null=True, blank=True)),
                ("meets_needs", models.IntegerField(null=True, blank=True)),
                ("recommend", models.IntegerField(null=True, blank=True)),
                ("better_decisions", models.IntegerField(null=True, blank=True)),
                ("reduces_time", models.IntegerField(null=True, blank=True)),
                ("improves_transparency", models.IntegerField(null=True, blank=True)),
                ("continue_using", models.IntegerField(null=True, blank=True)),
                ("prefer_over_traditional", models.IntegerField(null=True, blank=True)),
                ("like_most", models.TextField(blank=True)),
                ("challenges_exp", models.TextField(blank=True)),
                ("improvements", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]