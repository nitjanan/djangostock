# Generated by Django 3.2.5 on 2021-12-15 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0246_auto_20211214_1130'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('id',), 'verbose_name': 'หมวดหมู่สินค้า', 'verbose_name_plural': 'ข้อมูลประเภทสินค้า'},
        ),
        migrations.AddField(
            model_name='requisitionitem',
            name='is_receive',
            field=models.BooleanField(default=False),
        ),
    ]
