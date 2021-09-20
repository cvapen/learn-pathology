# Generated by Django 3.2 on 2021-09-20 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slide', '0002_annotatedslide_pointer'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='pathology',
            field=models.BooleanField(default=False, help_text='Does the slide show pathology or not'),
        ),
    ]
