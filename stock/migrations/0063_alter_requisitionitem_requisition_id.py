# Generated by Django 3.2.5 on 2021-07-20 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0062_basepermission_position_positionbasepermission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisitionitem',
            name='requisition_id',
            field=models.IntegerField(),
        ),
    ]
