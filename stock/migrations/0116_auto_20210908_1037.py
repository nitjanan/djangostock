# Generated by Django 3.2.5 on 2021-09-08 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0115_auto_20210908_1036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonpriceitem',
            name='unit',
            field=models.CharField(blank=True, default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='requisitionitem',
            name='unit',
            field=models.CharField(blank=True, default=1, max_length=255),
            preserve_default=False,
        ),
    ]
