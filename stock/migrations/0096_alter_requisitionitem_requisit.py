# Generated by Django 3.2.5 on 2021-08-23 07:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0095_requisitionitem_requisit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisitionitem',
            name='requisit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.requisition'),
        ),
    ]
