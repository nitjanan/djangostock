# Generated by Django 4.1.4 on 2024-07-24 08:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0027_basebranchcompany_bill_code'),
    ]

    operations = [
        migrations.RenameField(
            model_name='basebranchcompany',
            old_name='bill_code',
            new_name='invoice_code',
        ),
    ]