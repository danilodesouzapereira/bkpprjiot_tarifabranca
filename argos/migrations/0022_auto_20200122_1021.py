# Generated by Django 2.2.3 on 2020-01-22 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argos', '0021_auto_20200117_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='tr_account',
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='tr_value',
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
    ]
