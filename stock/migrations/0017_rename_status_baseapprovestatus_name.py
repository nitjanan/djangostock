# Generated by Django 3.2.3 on 2021-06-29 02:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0016_auto_20210628_1635'),
    ]

    operations = [
        migrations.RenameField(
            model_name='baseapprovestatus',
            old_name='status',
            new_name='name',
        ),
    ]
