# Generated by Django 3.2.5 on 2021-08-11 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0076_remove_purchaserequisition_stockman_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_express', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('address', models.TextField(blank=True)),
                ('tel', models.CharField(blank=True, max_length=255)),
                ('fax', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'verbose_name': 'ลูกค้า',
                'verbose_name_plural': 'ข้อมูลลูกค้า',
                'db_table': 'Customer',
                'ordering': ('id',),
            },
        ),
    ]
