# Generated by Django 4.1.4 on 2024-08-06 04:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0033_baseagency'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='agency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseagency'),
        ),
    ]
