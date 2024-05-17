# Generated by Django 3.2.5 on 2021-09-17 06:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0141_comparisonpricedistributor_vat_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='vat_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='stock.basevattype'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='vat_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='stock.basevattype'),
            preserve_default=False,
        ),
    ]