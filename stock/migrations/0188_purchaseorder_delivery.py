# Generated by Django 3.2.5 on 2021-11-10 06:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0187_basedelivery'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='delivery',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basedelivery'),
        ),
    ]
