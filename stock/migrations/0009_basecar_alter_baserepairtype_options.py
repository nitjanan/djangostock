# Generated by Django 4.1.4 on 2024-05-27 02:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0008_baserepairtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseCar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='ชื่อทะเบียนรถ')),
            ],
            options={
                'verbose_name': 'ทะเบียนรถ',
                'verbose_name_plural': 'ข้อมูลทะเบียนรถ',
                'db_table': 'BaseCar',
                'ordering': ('id',),
            },
        ),
        migrations.AlterModelOptions(
            name='baserepairtype',
            options={'ordering': ('id',), 'verbose_name': 'ประเภทการซ่อม', 'verbose_name_plural': 'ข้อมูลประเภทการซ่อม'},
        ),
    ]
