# Generated by Django 3.2.5 on 2021-08-23 02:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0090_alter_purchaseorderitem_item'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchaseorder',
            options={'ordering': ('-id',)},
        ),
        migrations.AlterModelOptions(
            name='purchaserequisition',
            options={'ordering': ('-id',)},
        ),
        migrations.AlterModelOptions(
            name='requisition',
            options={'ordering': ('-id',)},
        ),
    ]
