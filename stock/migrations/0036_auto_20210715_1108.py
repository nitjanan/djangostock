# Generated by Django 3.2.5 on 2021-07-15 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0035_auto_20210715_1058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisition',
            name='chief_approve_user_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='supplies_approve_user_name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
