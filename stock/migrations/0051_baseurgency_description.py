# Generated by Django 3.2.5 on 2021-07-17 03:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0050_alter_baseurgency_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseurgency',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
