# Generated by Django 3.2.5 on 2022-11-02 03:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0307_auto_20221102_0952'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseaffiliatedcompany',
            name='iso_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseisocode', verbose_name='รหัส iso'),
        ),
    ]
