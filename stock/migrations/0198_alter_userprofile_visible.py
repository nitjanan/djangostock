# Generated by Django 3.2.5 on 2021-11-12 07:33

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0197_userprofile_visible'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='visible',
            field=multiselectfield.db.fields.MultiSelectField(choices=[(1, 'Request'), (2, 'Approve'), (3, 'Receive')], max_length=5),
        ),
    ]
