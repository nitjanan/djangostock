# Generated by Django 4.1.4 on 2024-06-10 02:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0011_alter_purchaserequisition_note'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonprice',
            name='note',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='note',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='receive',
            name='note',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]