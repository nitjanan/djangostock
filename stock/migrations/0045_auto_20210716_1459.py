# Generated by Django 3.2.5 on 2021-07-16 07:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0044_purchaserequisition'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchaserequisition',
            options={'ordering': ('id',)},
        ),
        migrations.AlterModelTable(
            name='purchaserequisition',
            table='PurchaseRequisition',
        ),
    ]
