# Generated by Django 3.2.5 on 2022-01-07 07:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0263_distributor_vat_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basevattype',
            options={'ordering': ('id',), 'verbose_name': 'ชนิดภาษี', 'verbose_name_plural': 'ข้อมูลชนิดภาษี'},
        ),
    ]