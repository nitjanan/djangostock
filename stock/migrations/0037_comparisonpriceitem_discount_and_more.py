# Generated by Django 4.1.4 on 2024-08-09 03:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0036_rename_aagency_baseexpensedepartment_agency'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparisonpriceitem',
            name='discount',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='discount',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
