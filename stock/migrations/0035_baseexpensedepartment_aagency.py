# Generated by Django 4.1.4 on 2024-08-06 04:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0034_requisition_agency'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseexpensedepartment',
            name='aagency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseagency'),
        ),
    ]
