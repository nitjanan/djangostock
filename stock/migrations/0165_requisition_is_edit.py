# Generated by Django 3.2.5 on 2021-10-19 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0164_auto_20211018_0937'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='is_edit',
            field=models.BooleanField(default=True),
        ),
    ]