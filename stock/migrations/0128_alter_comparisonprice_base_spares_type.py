# Generated by Django 3.2.5 on 2021-09-14 03:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0127_comparisonprice_base_spares_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonprice',
            name='base_spares_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basesparestype'),
        ),
    ]
