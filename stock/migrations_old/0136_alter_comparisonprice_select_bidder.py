# Generated by Django 3.2.5 on 2021-09-15 07:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0135_requisitionitem_quantity_pr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonprice',
            name='select_bidder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.distributor'),
        ),
    ]