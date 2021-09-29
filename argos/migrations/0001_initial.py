# Generated by Django 2.0.2 on 2018-03-12 19:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dev_eui', models.CharField(max_length=50)),
                ('dev_pwd', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='DeviceType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dev_type_id', models.IntegerField(default=0)),
                ('dev_type_desc', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Payload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pl_pck', models.CharField(max_length=200)),
                ('pl_timestamp', models.IntegerField(default=0)),
                ('pl_datetime', models.DateTimeField()),
                ('dev_eui', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='argos.Device')),
            ],
        ),
        migrations.AddField(
            model_name='device',
            name='dev_type_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='argos.DeviceType'),
        ),
    ]
