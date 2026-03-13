from django.db import migrations, models


def create_sample_lodges(apps, schema_editor):
    ShortTermLodge = apps.get_model('properties', 'ShortTermLodge')
    ShortTermLodge.objects.create(
        name='Sample Lodge One',
        url='https://example.com',
        thumb_url='/static/images/shortterm.jpg',
        is_active=True,
        order=1,
    )
    ShortTermLodge.objects.create(
        name='Sample Lodge Two',
        url='https://example.org',
        thumb_url='/static/images/shortterm.jpg',
        is_active=True,
        order=2,
    )


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('properties', '0007_property_view_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShortTermLodge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(max_length=1000)),
                ('thumb_url', models.CharField(blank=True, help_text='Optional thumbnail URL or static path', max_length=1000)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RunPython(create_sample_lodges),
    ]
