# Generated by Django 3.2.5 on 2021-07-19 03:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0053_alter_purchaserequisition_requisition_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchaserequisition',
            name='requisition_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock.requisition'),
        ),
    ]