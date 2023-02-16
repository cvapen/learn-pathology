# Generated by Django 3.2.13 on 2023-02-02 09:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('slide', '0007_boundingbox'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='boundingbox',
            unique_together={('annotated_slide', 'position_x', 'position_y', 'width', 'height', 'text')},
        ),
        migrations.AlterUniqueTogether(
            name='pointer',
            unique_together={('annotated_slide', 'position_x', 'position_y', 'text')},
        ),
    ]