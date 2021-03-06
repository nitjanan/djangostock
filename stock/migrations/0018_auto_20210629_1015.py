# Generated by Django 3.2.3 on 2021-06-29 03:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0017_rename_status_baseapprovestatus_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisition',
            name='chief_approve_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chief_approve_status_set', to='stock.baseapprovestatus'),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='supplies_approve_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplies_approve_status', to='stock.baseapprovestatus'),
        ),
    ]
