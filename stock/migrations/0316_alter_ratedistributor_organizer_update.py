# Generated by Django 3.2.5 on 2023-02-27 03:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0315_ratedistributor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ratedistributor',
            name='organizer_update',
            field=models.DateField(auto_now_add=True, default=1),
            preserve_default=False,
        ),
    ]