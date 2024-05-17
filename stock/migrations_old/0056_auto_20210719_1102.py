# Generated by Django 3.2.5 on 2021-07-19 04:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0055_alter_purchaserequisition_requisition_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchaserequisition',
            name='requisition_id',
        ),
        migrations.AddField(
            model_name='purchaserequisition',
            name='requisition',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock.requisition', unique=True),
        ),
    ]