# Generated by Django 4.1.4 on 2025-04-02 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0066_invoiceitem_is_express_invoiceitem_v_stamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
