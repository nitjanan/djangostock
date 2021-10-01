# Generated by Django 3.2.5 on 2021-09-15 09:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock', '0137_alter_comparisonprice_base_spares_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparisonprice',
            name='approver_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cp_approver_status', to='stock.baseapprovestatus'),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='approver_update',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='approver_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cp_approver_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='examiner_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cp_examiner_status', to='stock.baseapprovestatus'),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='examiner_update',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='examiner_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cp_examiner_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
