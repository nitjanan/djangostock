# Generated by Django 3.2.5 on 2021-12-03 06:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0226_auto_20211203_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='prefix',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseprefix', to_field='name'),
        ),
    ]
