# Generated by Django 2.1.7 on 2019-07-19 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argos', '0016_auto_20190718_1723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payload',
            name='pl_data',
            field=models.CharField(max_length=256),
        ),
    ]
