# Generated by Django 3.2.3 on 2021-06-29 04:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0019_alter_requisitionitem_desired_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisitionitem',
            name='desired_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
