# Generated by Django 3.2.5 on 2021-08-16 08:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0082_purchaseorderitem_purchase_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaseorderitem',
            name='purchase_order',
        ),
    ]
