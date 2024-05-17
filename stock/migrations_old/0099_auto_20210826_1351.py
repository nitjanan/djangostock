# Generated by Django 3.2.5 on 2021-08-26 06:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock', '0098_requisitionitem_requisit'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='approver_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='approver_status_po', to='stock.baseapprovestatus'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='approver_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='approver_user_po', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='note',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='stockman_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stockman_user_po', to=settings.AUTH_USER_MODEL),
        ),
    ]