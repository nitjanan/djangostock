# Generated by Django 3.2.5 on 2022-01-07 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0264_alter_basevattype_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basepermission',
            name='ap_amount_max',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='ยอดเงินที่อนุมัติใบเปรียบเทียบมากสุด'),
        ),
    ]