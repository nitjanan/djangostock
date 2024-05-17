# Generated by Django 3.2.5 on 2021-09-29 09:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0157_alter_comparisonprice_ref_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonprice',
            name='approver_update',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonprice',
            name='examiner_update',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='approver_update',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
        migrations.AlterField(
            model_name='purchaserequisition',
            name='approver_update',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
        migrations.AlterField(
            model_name='purchaserequisition',
            name='purchase_update',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
        migrations.AlterField(
            model_name='purchaserequisition',
            name='stockman_update',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
        migrations.AlterField(
            model_name='requisitionitem',
            name='desired_date',
            field=models.DateField(blank=True, default=datetime.date.today, null=True),
        ),
    ]