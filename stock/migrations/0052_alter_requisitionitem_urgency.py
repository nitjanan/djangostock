# Generated by Django 3.2.5 on 2021-07-17 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0051_baseurgency_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisitionitem',
            name='urgency',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
