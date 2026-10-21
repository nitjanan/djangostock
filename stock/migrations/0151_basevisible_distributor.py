from django.db import migrations


def create_distributor_tab(apps, schema_editor):
    """แท็บการใช้งาน "Distributor" (UserProfile > การมองเห็นแท็ปการใช้งาน) = เห็นเมนูผู้จัดจำหน่าย ยกเว้นหน้าอนุมัติ"""
    BaseVisible = apps.get_model("stock", "BaseVisible")
    BaseVisible.objects.get_or_create(name="Distributor")


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0150_candidate_prefix_credit_contact'),
    ]

    operations = [
        # ย้อนกลับไม่ลบแท็บ: อาจมีผู้ใช้ถูกติ๊กแท็บนี้ไว้แล้ว
        migrations.RunPython(create_distributor_tab, migrations.RunPython.noop),
    ]
