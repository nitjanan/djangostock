# Generated by Django 3.2.5 on 2022-01-24 02:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0271_remove_purchaseorder_is_save'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseBranchCompany',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False, unique=True, verbose_name='รหัสสาขาบริษัท')),
                ('code', models.CharField(max_length=255, unique=True, verbose_name='โค้ดสาขาบริษัท')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='ชื่อสาขาบริษัท')),
                ('affiliated', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branch_affiliated', to='stock.baseaffiliatedcompany', verbose_name='ชื่อสังกัดบริษัท')),
            ],
            options={
                'verbose_name': 'สาขาบริษัท',
                'verbose_name_plural': 'ข้อมูลสาขาบริษัท',
                'db_table': 'BaseBranchCompany',
                'ordering': ('id',),
            },
        ),
    ]
