# Generated by Django 3.2.5 on 2021-09-22 02:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0145_auto_20210922_0951'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorder',
            name='credit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basecredit'),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='distributor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.distributor'),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='vat_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basevattype'),
        ),
    ]
