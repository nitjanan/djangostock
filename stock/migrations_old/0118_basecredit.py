# Generated by Django 3.2.5 on 2021-09-08 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0117_auto_20210908_1045'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseCredit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'verbose_name': 'เครดิต',
                'verbose_name_plural': 'ข้อมูลเครดิต',
                'db_table': 'BaseCredit',
                'ordering': ('id',),
            },
        ),
    ]