# Generated by Django 3.2.5 on 2021-12-03 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0230_baseprefix_prefix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='contact',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='fax',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='payment',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='tel',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
