# Generated by Django 3.2.5 on 2022-05-06 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0292_requisition_address_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserequisition',
            name='is_complete',
            field=models.BooleanField(default=False),
        ),
    ]
