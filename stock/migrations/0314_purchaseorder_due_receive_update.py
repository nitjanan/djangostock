# Generated by Django 3.2.5 on 2023-02-10 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0313_comparisonprice_amount_diff'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='due_receive_update',
            field=models.DateField(blank=True, null=True),
        ),
    ]
