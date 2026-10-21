from django.db.models.signals import post_save, pre_delete, pre_save

from stock.audit import log_delete, log_save, snapshot_old
from stock.models import (
    ComparisonPrice, ComparisonPriceDistributor, ComparisonPriceItem,
    PurchaseOrder, PurchaseOrderItem,
)

#ตารางที่เก็บ log การแก้ไข (DocumentChangeLog)
AUDITED_MODELS = (
    ComparisonPrice,
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    PurchaseOrder,
    PurchaseOrderItem,
)


def audit_pre_save(sender, instance, raw=False, **kwargs):
    if not raw:
        snapshot_old(instance)


def audit_post_save(sender, instance, created, raw=False, **kwargs):
    if not raw:
        log_save(instance, created)


def audit_pre_delete(sender, instance, **kwargs):
    log_delete(instance)


for model in AUDITED_MODELS:
    pre_save.connect(audit_pre_save, sender=model, dispatch_uid='audit_pre_save_' + model.__name__)
    post_save.connect(audit_post_save, sender=model, dispatch_uid='audit_post_save_' + model.__name__)
    #pre_delete เพื่อเก็บข้อมูลก่อนลบ (ตอนนี้แถวยังอยู่ และหาเลขที่เอกสารแม่ได้)
    pre_delete.connect(audit_pre_delete, sender=model, dispatch_uid='audit_pre_delete_' + model.__name__)
