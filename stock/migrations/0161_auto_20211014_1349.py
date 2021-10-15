# Generated by Django 3.2.5 on 2021-10-14 06:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0160_alter_purchaserequisition_table'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='baseapprovestatus',
            options={'ordering': ('id',), 'verbose_name': 'สถานะการอนุมัติ', 'verbose_name_plural': 'ข้อมูลสถานะการอนุมัติ'},
        ),
        migrations.AlterModelOptions(
            name='basevattype',
            options={'ordering': ('id',), 'verbose_name': 'ประเภทภาษี', 'verbose_name_plural': 'ข้อมูลประเภทภาษี'},
        ),
        migrations.AlterModelOptions(
            name='position',
            options={'ordering': ('id',), 'verbose_name': 'ประเภทตำแหน่งงาน', 'verbose_name_plural': 'ข้อมูลประเภทตำแหน่งงาน'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': 'ผู้ใช้และตำแหน่งงาน', 'verbose_name_plural': 'ข้อมูลผู้ใช้และตำแหน่งงาน'},
        ),
    ]
