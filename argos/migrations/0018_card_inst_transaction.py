# Generated by Django 2.2.3 on 2020-01-03 16:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('argos', '0017_auto_20190719_0947'),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_cod', models.CharField(max_length=10)),
                ('card_value', models.DecimalField(decimal_places=2, max_digits=4)),
                ('card_is_used', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Inst',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inst_cod', models.CharField(max_length=20)),
                ('inst_dev_eui', models.CharField(max_length=50)),
                ('inst_constant', models.IntegerField(default=2000)),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='argos.Device')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tr_date', models.DateTimeField()),
                ('tr_inst_cod', models.CharField(max_length=20)),
                ('tr_dev_eui', models.CharField(blank=True, default='', max_length=50)),
                ('tr_card_cod', models.CharField(blank=True, max_length=10, null=True)),
                ('tr_pulseC', models.IntegerField(default=0)),
                ('tr_value', models.DecimalField(decimal_places=2, max_digits=6)),
                ('tr_account', models.DecimalField(decimal_places=2, max_digits=6)),
                ('tr_action', models.CharField(max_length=20)),
                ('tr_status', models.CharField(max_length=20, null=True)),
                ('card', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='argos.Card')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='argos.Device')),
                ('inst', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='argos.Inst')),
            ],
        ),
    ]