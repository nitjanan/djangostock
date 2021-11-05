# Generated by Django 3.2.5 on 2021-11-04 07:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0184_receive_receive_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiveItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('unit_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created', models.DateField(auto_now_add=True)),
                ('update', models.DateField(auto_now=True)),
                ('item', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.requisitionitem')),
                ('rc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.receive')),
                ('unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='stock.baseunit')),
            ],
            options={
                'db_table': 'ReceiveItem',
                'ordering': ('id',),
            },
        ),
    ]
