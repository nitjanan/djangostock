# Generated by Django 3.2.5 on 2021-08-12 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0080_alter_purchaseorder_credit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='price',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='quantity',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='unit_price',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]