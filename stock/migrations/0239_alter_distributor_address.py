# Generated by Django 3.2.5 on 2021-12-08 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0238_alter_distributor_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
    ]
