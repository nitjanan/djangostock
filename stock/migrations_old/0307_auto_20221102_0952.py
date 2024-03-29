# Generated by Django 3.2.5 on 2022-11-02 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0306_baseisocode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseisocode',
            name='cm_code',
            field=models.CharField(max_length=255, verbose_name='รหัส iso ใบเปรียบเทียบ'),
        ),
        migrations.AlterField(
            model_name='baseisocode',
            name='po_code',
            field=models.CharField(max_length=255, verbose_name='รหัส iso ใบสั่งซื้อ'),
        ),
        migrations.AlterField(
            model_name='baseisocode',
            name='pr_code',
            field=models.CharField(max_length=255, verbose_name='รหัส iso ใบขอซื้อ'),
        ),
        migrations.AlterField(
            model_name='baseisocode',
            name='r_code',
            field=models.CharField(max_length=255, verbose_name='รหัส iso ใบขอเบิก'),
        ),
    ]
