# Generated by Django 3.2.5 on 2021-09-14 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0134_comparisonprice_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisitionitem',
            name='quantity_pr',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]