# Generated by Django 3.2.5 on 2022-04-20 06:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0287_baseadress'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='BaseAdress',
            new_name='BaseAddress',
        ),
        migrations.AlterModelTable(
            name='baseaddress',
            table='BaseAddress',
        ),
    ]