# Generated by Django 3.2.13 on 2022-09-27 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='long_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
