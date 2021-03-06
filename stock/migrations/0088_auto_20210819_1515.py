# Generated by Django 3.2.5 on 2021-08-19 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0087_purchaseorderitem_po'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='discount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='total_after_discount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='vat',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
    ]
