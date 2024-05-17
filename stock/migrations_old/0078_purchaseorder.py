# Generated by Django 3.2.5 on 2021-08-11 06:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0077_customer'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credit', models.CharField(max_length=255, unique=True)),
                ('shipping', models.CharField(blank=True, max_length=255)),
                ('created', models.DateField(auto_now_add=True)),
                ('update', models.DateField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.customer')),
            ],
            options={
                'db_table': 'PurchaseOrder',
                'ordering': ('id',),
            },
        ),
    ]