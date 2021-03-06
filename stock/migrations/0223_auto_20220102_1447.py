# Generated by Django 3.2.5 on 2022-01-02 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0222_alter_basegenretype_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseDistributorGenre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'ประเภทของผู้จัดจำหน่าย',
                'verbose_name_plural': 'ข้อมูลประเภทของผู้จัดจำหน่าย',
                'db_table': 'BaseDistributorGenre',
                'ordering': ('id',),
            },
        ),
        migrations.DeleteModel(
            name='BaseGenreType',
        ),
    ]
