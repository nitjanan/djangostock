# Generated by Django 3.2.5 on 2021-12-14 04:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0243_remove_product_id_express'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='affiliated',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseaffiliatedcompany'),
        ),
    ]
