import re

import django.db.models.deletion
from django.db import migrations, models


def credit_days_to_base_credit(apps, schema_editor):
    """เครดิตที่กรอกเป็นตัวเลขวัน -> แถวใน BaseCredit ที่ชื่อเป็น "<n> วัน" (ไม่มีแถวที่ตรงกัน = ว่าง)"""
    Candidate = apps.get_model("stock", "DistributorCandidate")
    BaseCredit = apps.get_model("stock", "BaseCredit")
    by_days = {}
    for credit in BaseCredit.objects.all():
        m = re.fullmatch(r"\s*(\d+)\s*วัน\s*", credit.name or "")
        if m:
            by_days.setdefault(int(m.group(1)), credit)
    for c in Candidate.objects.exclude(credit_days=None):
        c.credit = by_days.get(c.credit_days)
        c.save(update_fields=["credit"])


def base_credit_to_credit_days(apps, schema_editor):
    Candidate = apps.get_model("stock", "DistributorCandidate")
    for c in Candidate.objects.exclude(credit=None).select_related("credit"):
        m = re.match(r"\s*(\d+)", c.credit.name or "")
        c.credit_days = int(m.group(1)) if m else None
        c.save(update_fields=["credit_days"])


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0149_place_source_manual'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributorcandidate',
            name='prefix',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock.baseprefix', verbose_name='คำนำหน้า'),
        ),
        migrations.AddField(
            model_name='distributorcandidate',
            name='credit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock.basecredit', verbose_name='เครดิต'),
        ),
        migrations.RunPython(credit_days_to_base_credit, base_credit_to_credit_days),
        migrations.RemoveField(
            model_name='distributorcandidate',
            name='credit_days',
        ),
        # ช่องเดิม "โทรสาร / LINE ID" -> โทรสาร (ค่าเดิมอยู่ช่องนี้) + ช่องทางติดต่ออื่นๆ ช่องใหม่ (LINE / Facebook ฯลฯ)
        migrations.RenameField(
            model_name='distributorcandidate',
            old_name='fax_line',
            new_name='fax',
        ),
        migrations.AlterField(
            model_name='distributorcandidate',
            name='fax',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='โทรสาร'),
        ),
        migrations.AddField(
            model_name='distributorcandidate',
            name='other_contact',
            field=models.TextField(blank=True, null=True, verbose_name='ช่องทางติดต่ออื่นๆ'),
        ),
        migrations.AddField(
            model_name='distributor',
            name='other_contact',
            field=models.TextField(blank=True, null=True, verbose_name='ช่องทางติดต่ออื่นๆ'),
        ),
    ]
