# Generated by Django 3.2.3 on 2021-06-08 07:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_auto_20210525_1129'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('postcode', models.CharField(blank=True, max_length=255)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('email', models.EmailField(blank=True, max_length=250)),
                ('token', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'db_table': 'Order',
            },
        ),
        migrations.AlterModelOptions(
            name='cart',
            options={'ordering': ('date_add',), 'verbose_name': 'ตะกร้าสินค้า', 'verbose_name_plural': 'ข้อมูลตะกร้าสินค้า'},
        ),
        migrations.AlterModelOptions(
            name='cartitem',
            options={'verbose_name': 'รายการตะกร้าสินค้า', 'verbose_name_plural': 'ข้อมูลรายการตะกร้าสินค้า'},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.CharField(max_length=250)),
                ('quantity', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stock.order')),
            ],
            options={
                'db_table': 'OrderItem',
            },
        ),
    ]
