# Generated by Django 4.1.4 on 2024-07-01 02:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0014_requisition_broke_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseRequisitionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='ชื่อประเภทใบขอเบิก')),
            ],
            options={
                'verbose_name': 'ประเภทใบขอเบิก',
                'verbose_name_plural': 'ข้อมูลประเภทใบขอเบิก',
                'db_table': 'BaseRequisitionType',
                'ordering': ('id',),
            },
        ),
    ]
