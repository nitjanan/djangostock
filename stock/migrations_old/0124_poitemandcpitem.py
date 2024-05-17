# Generated by Django 3.2.5 on 2021-09-10 08:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0123_purchaseorderitem_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='POItemAndCPItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cp_item', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.comparisonpriceitem')),
                ('po_item', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.purchaseorderitem')),
            ],
            options={
                'db_table': 'POItemAndCPItem',
                'ordering': ('id',),
            },
        ),
    ]