# Generated by Django 3.2.5 on 2022-01-07 03:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0262_alter_basevattype_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributor',
            name='vat_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basevattype', verbose_name='ชนิดภาษี'),
        ),
    ]
