# Generated by Django 3.2.5 on 2022-03-03 01:49

from django.db import migrations, models
import stock.models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0283_alter_purchaseorder_ref_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonprice',
            name='ref_no',
            field=models.CharField(blank=True, default=stock.models.comparisonPrice_ref_number, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='ref_no',
            field=models.CharField(blank=True, default=stock.models.purchaseOrder_ref_number, max_length=255, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='purchaserequisition',
            name='ref_no',
            field=models.CharField(blank=True, default=stock.models.purchaseRequisition_ref_number, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='receive',
            name='ref_no',
            field=models.CharField(blank=True, default=stock.models.receive_ref_number, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='pr_ref_no',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='ref_no',
            field=models.CharField(blank=True, default=stock.models.requisition_ref_number, max_length=255, null=True),
        ),
    ]
