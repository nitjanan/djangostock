# Generated by Django 4.1.4 on 2024-02-16 08:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0003_remove_document_test'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributor',
            name='created',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='วันที่สร้าง'),
        ),
    ]
