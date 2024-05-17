# Generated by Django 3.2.3 on 2021-06-21 09:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('stock', '0005_auto_20210609_1043'),
    ]

    operations = [
        migrations.CreateModel(
            name='requisitionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requisition_id', models.CharField(blank=True, max_length=255)),
                ('product_name', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('quantity', models.IntegerField()),
                ('machine', models.CharField(max_length=255)),
                ('created', models.DateField(auto_now_add=True)),
                ('update', models.DateField(auto_now=True)),
                ('desired_date', models.DateField()),
            ],
            options={
                'db_table': 'RequisitionItem',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='requisition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('created', models.DateField(auto_now_add=True)),
                ('update', models.DateField(auto_now=True)),
                ('reference_id', models.CharField(max_length=255)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group')),
            ],
            options={
                'db_table': 'Requisition',
                'ordering': ('id',),
            },
        ),
    ]