# Generated by Django 3.2.5 on 2021-10-20 02:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0165_requisition_is_edit'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='signature',
            field=models.ImageField(blank=True, null=True, upload_to='signature/'),
        ),
    ]
