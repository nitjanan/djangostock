# Generated by Django 3.2.5 on 2022-10-24 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0302_alter_requisitionitem_quantity_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='positionbasepermission',
            name='branch_company',
            field=models.ManyToManyField(to='stock.BaseBranchCompany', verbose_name='สิทธิการอนุมัติตามบริษัท'),
        ),
    ]
