# Generated by Django 3.2.5 on 2021-09-23 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0151_alter_purchaseorder_ref_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserequisition',
            name='ref_no',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
