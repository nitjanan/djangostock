# Generated by Django 4.1.4 on 2024-06-19 02:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0013_basebroketype'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='broke_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.basebroketype'),
        ),
    ]