# Generated by Django 3.2.5 on 2021-07-15 04:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock', '0042_auto_20210715_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requisition',
            name='chief_approve_user_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chief_approve_user_name', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='name', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='supplies_approve_user_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplies_approve_user_name', to=settings.AUTH_USER_MODEL),
        ),
    ]
