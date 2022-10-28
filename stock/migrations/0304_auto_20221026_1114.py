# Generated by Django 3.2.5 on 2022-10-26 04:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock', '0303_positionbasepermission_branch_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='comparisonprice',
            name='special_approver_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cp_special_approver_status', to='stock.baseapprovestatus'),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='special_approver_update',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='comparisonprice',
            name='special_approver_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cp_special_approver_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
