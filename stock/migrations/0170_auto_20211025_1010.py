# Generated by Django 3.2.5 on 2021-10-25 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0169_auto_20211025_1009'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='positionbasepermission',
            name='ap_amount_max',
        ),
        migrations.RemoveField(
            model_name='positionbasepermission',
            name='ap_amount_min',
        ),
        migrations.AddField(
            model_name='basepermission',
            name='ap_amount_max',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='basepermission',
            name='ap_amount_min',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
