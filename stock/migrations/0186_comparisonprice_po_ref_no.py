# Generated by Django 3.2.5 on 2021-11-10 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0185_receiveitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparisonprice',
            name='po_ref_no',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]