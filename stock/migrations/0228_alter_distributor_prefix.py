# Generated by Django 3.2.5 on 2021-12-03 06:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0227_alter_distributor_prefix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='prefix',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseprefix'),
        ),
    ]
