# Generated by Django 3.2.3 on 2021-07-05 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0024_auto_20210701_1003'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='chief_approve_user_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='requisition',
            name='supplies_approve_user_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
