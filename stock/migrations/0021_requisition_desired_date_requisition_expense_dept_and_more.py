# Generated by Django 4.1.4 on 2024-07-05 03:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0020_baseexpensedepartment'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='desired_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='requisition',
            name='expense_dept',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseexpensedepartment'),
        ),
        migrations.AddField(
            model_name='requisition',
            name='is_invoice',
            field=models.BooleanField(default=False),
        ),
    ]
