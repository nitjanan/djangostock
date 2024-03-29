# Generated by Django 3.2.5 on 2023-02-24 08:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock', '0314_purchaseorder_due_receive_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='RateDistributor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_rate', models.IntegerField(blank=True, null=True)),
                ('quantity_rate', models.IntegerField(blank=True, null=True)),
                ('duration_rate', models.IntegerField(blank=True, null=True)),
                ('service_rate', models.IntegerField(blank=True, null=True)),
                ('safety_rate', models.IntegerField(blank=True, null=True)),
                ('total_rate', models.IntegerField(blank=True, null=True)),
                ('organizer_update', models.DateField(blank=True, null=True)),
                ('distributor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.distributor')),
                ('organizer_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rate_organizer_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'RateDistributor',
                'ordering': ('id',),
            },
        ),
    ]
