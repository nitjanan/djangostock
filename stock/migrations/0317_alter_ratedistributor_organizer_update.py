# Generated by Django 3.2.5 on 2023-02-27 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0316_alter_ratedistributor_organizer_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ratedistributor',
            name='organizer_update',
            field=models.DateField(auto_now=True),
        ),
    ]
