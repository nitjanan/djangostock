# Generated by Django 3.2.5 on 2021-11-23 04:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0214_alter_comparisonpricedistributor_discount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comparisonpricedistributor',
            name='discount',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]