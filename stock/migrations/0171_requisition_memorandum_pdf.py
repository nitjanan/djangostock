# Generated by Django 3.2.5 on 2021-10-28 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0170_auto_20211025_1010'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='memorandum_pdf',
            field=models.FileField(blank=True, null=True, upload_to='pdfs/requisition/'),
        ),
    ]
