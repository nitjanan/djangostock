# Generated by Django 3.2.5 on 2021-12-03 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0224_baseaffiliatedcompany'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasePrefix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'คำนำหน้านาม',
                'verbose_name_plural': 'ข้อมูลคำนำหน้านาม',
                'db_table': 'BasePrefix',
                'ordering': ('id',),
            },
        ),
    ]
