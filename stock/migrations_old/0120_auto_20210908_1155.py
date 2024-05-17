# Generated by Django 3.2.5 on 2021-09-08 04:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0119_alter_requisitionitem_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='credit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basecredit'),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='credit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basecredit'),
        ),
    ]