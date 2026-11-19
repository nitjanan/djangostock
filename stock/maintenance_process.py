"""เส้นทางเอกสารของใบแจ้งซ่อม: ใบแจ้งซ่อม -> ใบขอเบิก -> (ใบจ่ายสินค้าภายใน | ใบขอซื้อ -> เปรียบเทียบราคา -> ใบสั่งซื้อ -> รับของ)
และอะไหล่ที่ใช้ (จ่ายจากสต็อกใน Express + ซื้อตามใบสั่งซื้อ) ดู stock/maintenance_parts.py

ใช้กับ API ของ dashboard (getapiMaintenanceProcess) ให้รู้ว่าใบแจ้งซ่อมแต่ละใบค้างอยู่ขั้นไหน

ใบสั่งซื้อ/ใบเปรียบเทียบราคาผูกกับใบขอเบิกผ่านรายการสินค้า (RequisitionItem.requisit)
เพราะ PO ที่ออกจากใบเปรียบเทียบราคาไม่มี pr_id
"""
from collections import defaultdict

from stock.maintenance_parts import collect_parts, collect_po_parts
from stock.models import (
    ComparisonPrice,
    ComparisonPriceItem,
    Invoice,
    Maintenance,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
)

# BaseApproveStatus
STATUS_PENDING = 1
STATUS_APPROVED = 2
STATUS_REJECTED = 3
STATUS_NOT_PROCEED = 4

STATUS_NAMES = {
    STATUS_PENDING: "pending",
    STATUS_APPROVED: "approved",
    STATUS_REJECTED: "rejected",
    STATUS_NOT_PROCEED: "not_proceed",
}


def _iso(value):
    return value.isoformat() if value else None


def _status(status_id):
    return STATUS_NAMES.get(status_id, "pending")


def pr_status(purchase_status_id, approver_status_id):
    """ใบขอซื้อต้องผ่านทั้งเจ้าหน้าที่จัดซื้อ (purchase) และผู้อนุมัติ (approver)"""
    if STATUS_REJECTED in (purchase_status_id, approver_status_id):
        return "rejected"
    if STATUS_NOT_PROCEED in (purchase_status_id, approver_status_id):
        return "not_proceed"
    if purchase_status_id == STATUS_APPROVED and approver_status_id == STATUS_APPROVED:
        return "approved"
    return "pending"


def _group_by_requisition(rows, rq_key, doc_key):
    """[(rq_id, doc), ...] -> {rq_id: [doc ไม่ซ้ำ]}"""
    result = defaultdict(dict)
    for row in rows:
        result[row[rq_key]].setdefault(row[doc_key], row)
    return result


def collect_maintenance_process(start_date, end_date):
    mas = list(
        Maintenance.objects.filter(
            is_cancel=False,
            car__isnull=False,
            created__date__range=(start_date, end_date),
        )
        .values(
            "id", "ref_no", "broke_reason", "approve_status", "approve_update",
            "start_rp", "end_rp", "chief_update", "is_complete",
        )
        .order_by("id")
    )
    ma_ids = [m["id"] for m in mas]

    rqs = list(
        Requisition.objects.filter(ma_id__in=ma_ids)
        .values("id", "ma_id", "ref_no", "created")
        .order_by("id")
    )
    rq_ids = [r["id"] for r in rqs]

    prs = PurchaseRequisition.objects.filter(requisition_id__in=rq_ids, is_draft=False).values(
        "id", "requisition_id", "ref_no", "created", "purchase_status_id",
        "approver_status_id", "approver_update", "is_complete",
    )
    prs_by_rq = defaultdict(list)
    for pr in prs.order_by("id"):
        prs_by_rq[pr["requisition_id"]].append(pr)

    # ComparisonPriceItem.cp เป็น IntegerField ไม่ใช่ FK จึง join เองด้วย id
    cp_links = list(
        ComparisonPriceItem.objects.filter(item__requisit_id__in=rq_ids, cp__isnull=False)
        .values("item__requisit_id", "cp")
        .distinct()
    )
    cps = {
        cp["id"]: cp
        for cp in ComparisonPrice.objects.filter(id__in={link["cp"] for link in cp_links}).values(
            "id", "ref_no", "created", "approver_status_id", "approver_update"
        )
    }
    cps_by_rq = defaultdict(dict)
    for link in sorted(cp_links, key=lambda link: link["cp"]):
        cp = cps.get(link["cp"])
        if cp:
            cps_by_rq[link["item__requisit_id"]][cp["id"]] = cp

    pos_by_rq = _group_by_requisition(
        PurchaseOrderItem.objects.filter(
            item__requisit_id__in=rq_ids, po__isnull=False, po__is_cancel=False, po__is_draft=False
        )
        .values(
            "item__requisit_id", "po_id", "po__ref_no", "po__created", "po__approver_status_id",
            "po__approver_update", "po__is_receive", "po__receive_update",
            "po__due_receive_update", "po__amount",
        )
        .order_by("po_id"),
        "item__requisit_id",
        "po_id",
    )

    ivs_by_rq = defaultdict(list)
    for iv in Invoice.objects.filter(requisit_id__in=rq_ids).values(
        "id", "requisit_id", "ref_no", "created"
    ).order_by("id"):
        ivs_by_rq[iv["requisit_id"]].append(iv)

    rqs_by_ma = defaultdict(list)
    for rq in rqs:
        rqs_by_ma[rq["ma_id"]].append(rq)

    # อะไหล่จากใบจ่ายสินค้าภายใน (Express) — None = ต่อ Express ไม่ได้
    parts = collect_parts([ma["ref_no"] for ma in mas], start_date, end_date)
    po_parts = collect_po_parts(rq_ids)

    result = []
    for ma in mas:
        requisitions = []
        for rq in rqs_by_ma[ma["id"]]:
            rq_id = rq["id"]
            requisitions.append({
                "id": rq_id,
                "ref_no": rq["ref_no"],
                "created": _iso(rq["created"]),
                "invoices": [
                    {"id": iv["id"], "ref_no": iv["ref_no"], "created": _iso(iv["created"])}
                    for iv in ivs_by_rq[rq_id]
                ],
                "purchase_requisitions": [
                    {
                        "id": pr["id"],
                        "ref_no": pr["ref_no"],
                        "created": _iso(pr["created"]),
                        "status": pr_status(pr["purchase_status_id"], pr["approver_status_id"]),
                        "approver_update": _iso(pr["approver_update"]),
                        "is_complete": pr["is_complete"],
                    }
                    for pr in prs_by_rq[rq_id]
                ],
                "comparisons": [
                    {
                        "id": cp["id"],
                        "ref_no": cp["ref_no"],
                        "created": _iso(cp["created"]),
                        "status": _status(cp["approver_status_id"]),
                        "approver_update": _iso(cp["approver_update"]),
                    }
                    for cp in cps_by_rq[rq_id].values()
                ],
                "purchase_orders": [
                    {
                        "id": po["po_id"],
                        "ref_no": po["po__ref_no"],
                        "created": _iso(po["po__created"]),
                        "status": _status(po["po__approver_status_id"]),
                        "approver_update": _iso(po["po__approver_update"]),
                        "is_receive": po["po__is_receive"],
                        "receive_update": _iso(po["po__receive_update"]),
                        "due_receive_update": _iso(po["po__due_receive_update"]),
                        "amount": float(po["po__amount"]) if po["po__amount"] is not None else None,
                    }
                    for po in pos_by_rq[rq_id].values()
                ],
            })

        result.append({
            "id": ma["id"],
            "ref_no": ma["ref_no"],
            "broke_reason": ma["broke_reason"],
            # ขออนุมัติซ่อมบำรุง / อนุมัติซ่อมบำรุง / ไม่อนุมัติซ่อมบำรุง
            "approve_status": ma["approve_status"],
            "approve_update": _iso(ma["approve_update"]),
            "start_rp": _iso(ma["start_rp"]),
            "end_rp": _iso(ma["end_rp"]),
            "chief_update": _iso(ma["chief_update"]),
            "is_complete": ma["is_complete"],
            "requisitions": requisitions,
            "parts": {
                # None = ต่อ Express ไม่ได้ (ไม่รู้ ไม่ใช่ไม่มี)
                "issued": None if parts is None else parts.get((ma["ref_no"] or "").upper(), []),
                "purchased": [p for rq in rqs_by_ma[ma["id"]] for p in po_parts[rq["id"]]],
            },
        })
    return result
