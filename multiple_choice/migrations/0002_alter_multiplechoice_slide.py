# Generated by Django 3.2 on 2021-09-01 08:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('slide', '0002_annotatedslide_pointer'),
        ('multiple_choice', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multiplechoice',
            name='slide',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='slide.annotatedslide'),
        ),
    ]