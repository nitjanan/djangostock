# Generated by Django 3.2.5 on 2023-02-10 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0312_document'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparisonprice',
            name='amount_diff',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
