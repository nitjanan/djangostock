# Generated by Django 3.2.5 on 2021-11-16 04:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0205_auto_20211116_0927'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisitionitem',
            name='is_used',
            field=models.BooleanField(default=False),
        ),
    ]
