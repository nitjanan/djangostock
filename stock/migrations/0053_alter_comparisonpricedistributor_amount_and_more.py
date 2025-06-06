# Generated by Django 4.1.4 on 2025-01-06 03:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0052_alter_comparisonpriceitem_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='freight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='vat',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
    ]
