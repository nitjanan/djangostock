# Generated by Django 3.2.5 on 2021-12-10 04:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0240_alter_distributor_tex'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='receive_update',
            field=models.DateField(blank=True, null=True),
        ),
    ]
