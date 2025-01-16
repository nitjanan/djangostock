# Generated by Django 4.1.4 on 2025-01-15 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0062_alter_purchaseorder_approver_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basepermission',
            name='ap_amount_max',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='ยอดเงินที่อนุมัติใบเปรียบเทียบมากสุด'),
        ),
        migrations.AlterField(
            model_name='comparisonprice',
            name='amount_diff',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='freight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='total_after_discount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='vat',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpriceitem',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpriceitem',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='comparisonpriceitem',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='ราคา'),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='freight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='total_after_discount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='vat',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='requisitionitem',
            name='quantity',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='requisitionitem',
            name='quantity_pr',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='requisitionitem',
            name='quantity_take',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name='requisitionitem',
            name='quantity_used',
            field=models.DecimalField(blank=True, decimal_places=4, default=0.0, max_digits=12, null=True),
        ),
    ]
