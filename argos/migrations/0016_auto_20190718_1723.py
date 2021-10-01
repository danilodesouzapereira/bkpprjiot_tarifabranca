# Generated by Django 2.1.7 on 2019-07-18 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argos', '0015_devicetype_dev_type_interval'),
    ]

    operations = [
        migrations.AddField(
            model_name='payload',
            name='pl_rssi',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payload',
            name='pl_snr',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='servertype',
            name='server_type_data_format',
            field=models.CharField(default=1, max_length=20),
            preserve_default=False,
        ),
    ]