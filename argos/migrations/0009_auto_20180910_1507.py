# Generated by Django 2.0.2 on 2018-09-10 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argos', '0008_auto_20180829_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payload',
            name='pl_datetime',
            field=models.DateTimeField(),
        ),
    ]
