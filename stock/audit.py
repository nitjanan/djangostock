"""บันทึก log การแก้ไขใบเปรียบเทียบราคา / ใบสั่งซื้อ และรายการ item (DocumentChangeLog)

ผูกกับ signals pre_save / post_save / pre_delete ใน stock/signals.py
user ที่แก้ไขได้มาจาก AuditUserMiddleware (เก็บ request ปัจจุบันไว้ใน contextvar)
หมายเหตุ: QuerySet.update() ไม่ส่ง signal จึงไม่ถูกบันทึก
"""
import datetime
import decimal
import logging
from contextvars import ContextVar

from django.db import models, transaction

logger = logging.getLogger(__name__)

_audit_request = ContextVar('audit_request', default=None)

#field ที่เปลี่ยนเองอัตโนมัติ ไม่ต้องเก็บ log
IGNORED_FIELDS = {'update', 'qr_code'}


def set_audit_request(request):
    return _audit_request.set(request)


def reset_audit_request(token):
    _audit_request.reset(token)


def _current_user_and_path():
    request = _audit_request.get()
    if request is None:
        return None, ''
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        user = None
    return user, (request.path or '')[:255]


def _tracked_fields(instance):
    return [
        f for f in instance._meta.concrete_fields
        if not f.primary_key and f.name not in IGNORED_FIELDS
    ]


def _to_json(value):
    """แปลงค่าให้เก็บลง JSONField ได้"""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()
    if hasattr(value, 'name') and hasattr(value, 'storage'):  # FieldFile
        return value.name or None
    return str(value)


def _display(field, raw):
    """ค่าที่อ่านง่าย: FK แสดงเป็น "id: ชื่อ" """
    if raw is None or raw == '':
        return _to_json(raw)
    if isinstance(field, models.ForeignKey):
        try:
            obj = field.related_model._default_manager.filter(pk=raw).first()
        except Exception:
            obj = None
        return '{}: {}'.format(raw, obj) if obj is not None else _to_json(raw)
    return _to_json(raw)


def snapshot_old(instance):
    """pre_save: เก็บค่าเดิมจากฐานข้อมูลไว้บน instance เพื่อนำไปเทียบใน post_save"""
    instance._audit_old = None
    if instance.pk is None:
        return
    attnames = [f.attname for f in _tracked_fields(instance)]
    try:
        instance._audit_old = type(instance)._default_manager.filter(pk=instance.pk).values(*attnames).first()
    except Exception:
        logger.exception('DocumentChangeLog: อ่านค่าเดิมไม่สำเร็จ')


def _python_value(field, value):
    """แปลงค่าเป็นชนิดของ field (เช่น DateField(default=timezone.now) ในหน่วยความจำเป็น datetime แต่ในฐานข้อมูลเป็น date)"""
    try:
        return field.to_python(value)
    except Exception:
        return value


def _normalize(value):
    """เทียบค่าแบบไม่สนชนิดข้อมูล (เช่น Decimal('1.00') กับ '1.00' จากฟอร์ม)"""
    value = _to_json(value)
    if value == '':
        return None
    if isinstance(value, str):
        try:
            return decimal.Decimal(value)
        except decimal.InvalidOperation:
            return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return decimal.Decimal(str(value))
    return value


def _diff(instance, old):
    changes = {}
    for f in _tracked_fields(instance):
        old_raw = _python_value(f, old.get(f.attname))
        new_raw = _python_value(f, getattr(instance, f.attname))
        if _normalize(old_raw) != _normalize(new_raw):
            changes[f.name] = {'old': _display(f, old_raw), 'new': _display(f, new_raw)}
    return changes


def _full(instance):
    """ค่าทั้งหมดของรายการ (ใช้ตอนสร้าง) เก็บเฉพาะช่องที่มีค่า"""
    data = {}
    for f in _tracked_fields(instance):
        raw = _python_value(f, getattr(instance, f.attname))
        if raw is None or raw == '':
            continue
        data[f.name] = _display(f, raw)
    return data


def _resolve_document(instance):
    """หาเอกสารแม่ (ประเภท, id, เลขที่) ของรายการที่ถูกแก้ไข"""
    from stock.models import (
        ComparisonPrice, ComparisonPriceDistributor, ComparisonPriceItem,
        PurchaseOrder, PurchaseOrderItem,
    )

    def cp_ref(cp_id):
        if not cp_id:
            return ''
        return ComparisonPrice.objects.filter(pk=cp_id).values_list('ref_no', flat=True).first() or ''

    def po_ref(po_id):
        if not po_id:
            return ''
        return PurchaseOrder.objects.filter(pk=po_id).values_list('ref_no', flat=True).first() or ''

    if isinstance(instance, ComparisonPrice):
        return 'CP', instance.pk, instance.ref_no or ''
    if isinstance(instance, ComparisonPriceDistributor):
        return 'CP', instance.cp_id, cp_ref(instance.cp_id)
    if isinstance(instance, ComparisonPriceItem):
        #ComparisonPriceItem.cp เป็น IntegerField (id ใบเปรียบเทียบ) ไม่ใช่ FK
        cp_id = instance.cp
        if not cp_id and instance.bidder_id:
            cp_id = ComparisonPriceDistributor.objects.filter(pk=instance.bidder_id).values_list('cp_id', flat=True).first()
        return 'CP', cp_id, cp_ref(cp_id)
    if isinstance(instance, PurchaseOrder):
        return 'PO', instance.pk, instance.ref_no or ''
    if isinstance(instance, PurchaseOrderItem):
        return 'PO', instance.po_id, po_ref(instance.po_id)
    return None, None, ''


def _write(instance, action, changes):
    from stock.models import DocumentChangeLog

    doc_type, doc_id, doc_ref_no = _resolve_document(instance)
    if doc_type is None:
        return
    user, path = _current_user_and_path()
    #savepoint: ถ้าบันทึก log ไม่สำเร็จ จะไม่ทำให้ transaction ของการบันทึกเอกสารเสีย
    with transaction.atomic():
        DocumentChangeLog.objects.create(
            doc_type=doc_type,
            doc_id=doc_id,
            doc_ref_no=(doc_ref_no or '')[:255],
            model_name=type(instance).__name__,
            object_id=instance.pk,
            object_repr=str(instance)[:255],
            action=action,
            changes=changes,
            user=user,
            path=path,
        )


def log_save(instance, created):
    """post_save: บันทึกการสร้าง หรือการแก้ไข (เฉพาะเมื่อมีช่องที่เปลี่ยนจริง)"""
    try:
        old = getattr(instance, '_audit_old', None)
        if created or old is None:
            _write(instance, 'create', _full(instance))
        else:
            changes = _diff(instance, old)
            if changes:
                _write(instance, 'update', changes)
    except Exception:
        #log ห้ามทำให้การบันทึกเอกสารล้มเหลว
        logger.exception('DocumentChangeLog: บันทึก log ไม่สำเร็จ')


def _before_delete(instance):
    """ข้อมูลทั้งแถวก่อนลบ อ่านจากฐานข้อมูลโดยตรง เก็บทุกช่อง (รวมช่องว่าง, created, update, ไฟล์)"""
    fields = [f for f in instance._meta.concrete_fields if not f.primary_key]
    row = None
    try:
        row = type(instance)._default_manager.filter(pk=instance.pk).values(*[f.attname for f in fields]).first()
    except Exception:
        logger.exception('DocumentChangeLog: อ่านข้อมูลก่อนลบไม่สำเร็จ')
    data = {}
    for f in fields:
        raw = row.get(f.attname) if row is not None else getattr(instance, f.attname)
        data[f.name] = _display(f, _python_value(f, raw))
    return data


def log_delete(instance):
    """pre_delete: เก็บข้อมูลก่อนลบ (ถ้าการลบ rollback log นี้ก็ rollback ไปด้วย)"""
    try:
        _write(instance, 'delete', _before_delete(instance))
    except Exception:
        logger.exception('DocumentChangeLog: บันทึก log การลบไม่สำเร็จ')
