# Generated by Django 4.1.4 on 2025-02-10 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0063_alter_basepermission_ap_amount_max_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='r_qr_codes/', verbose_name='qr code'),
        ),
    ]
