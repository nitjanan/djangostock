# Generated by Django 4.1.4 on 2024-07-17 07:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0024_requisition_expenses'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requisition',
            name='is_invoice',
        ),
    ]