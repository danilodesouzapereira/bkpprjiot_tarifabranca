# Generated by Django 3.2.6 on 2021-10-01 11:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argos', '0028_auto_20210930_2007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxicms',
            name='datetime_fin',
        ),
        migrations.RemoveField(
            model_name='taxicms',
            name='datetime_ini',
        ),
        migrations.RemoveField(
            model_name='taxpiscofins',
            name='datetime_fin',
        ),
        migrations.RemoveField(
            model_name='taxpiscofins',
            name='datetime_ini',
        ),
        migrations.AddField(
            model_name='taxicms',
            name='month',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='taxicms',
            name='year',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='taxpiscofins',
            name='month',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='taxpiscofins',
            name='year',
            field=models.IntegerField(default=0),
        ),
    ]
