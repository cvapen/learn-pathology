# Generated by Django 3.2.13 on 2022-09-29 12:01

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0002_course_long_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='learning_outcomes',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='long_description',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]