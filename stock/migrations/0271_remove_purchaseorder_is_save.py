# Generated by Django 3.2.5 on 2022-01-18 04:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0270_purchaseorder_is_save'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaseorder',
            name='is_save',
        ),
    ]
