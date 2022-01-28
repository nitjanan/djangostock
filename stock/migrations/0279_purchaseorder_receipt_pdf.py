# Generated by Django 3.2.5 on 2022-01-28 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0278_auto_20220128_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='receipt_pdf',
            field=models.FileField(blank=True, null=True, upload_to='pdfs/receipt/RC_PO/%Y/%m/%d'),
        ),
    ]
