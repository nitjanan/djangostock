# Generated by Django 3.2.5 on 2021-12-14 03:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0242_alter_product_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='id_express',
        ),
    ]
