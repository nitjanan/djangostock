"""อะไหล่ที่ใช้ในการซ่อมแต่ละครั้ง มาจาก 2 ทาง

1. ใบจ่ายสินค้าภายใน-อะไหล่ ในโปรแกรมบัญชี Express (pg_db) — ของที่เบิกจากสต็อก
2. ใบสั่งซื้อที่ออกจากใบขอเบิกของใบแจ้งซ่อม — ของที่ซื้อมาใช้ซ่อม
   (รายการขอเบิกแยกจำนวนที่จ่ายจากสต็อก quantity_take กับที่ขอซื้อ quantity_pr จึงไม่นับซ้ำกัน)

ExOESTNH.note3 เก็บเลขที่ใบแจ้งซ่อม (Maintenance.ref_no) — เริ่มกรอกตั้งแต่ปี 2569 และยังไม่ครบทุกบริษัท
ใบจ่ายอะไหล่ = docnum ขึ้นต้นด้วย BaseBranchCompany.invoice_code และ comcod = ชื่อสังกัดบริษัท
(เหมือนหน้า Excel ใบจ่ายสินค้าภายใน-อะไหล่)
"""
import logging
import re
from collections import defaultdict

from django.db import DatabaseError, connections
from django.db.models import Q
from django.db.utils import ConnectionDoesNotExist

from stock.models import BaseBranchCompany, ExOESTND, ExOESTNH, Product, PurchaseOrderItem

logger = logging.getLogger(__name__)

# M + รหัสสาขา 2 ตัว + ปีเดือน พ.ศ. 4 หลัก + ลำดับ 3 หลัก เช่น MR16910004 (ดู maintenance_ref_number)
MA_REF_RE = re.compile(r"M[A-Z0-9]{2}\d{7}")
MA_REF_SQL = "M[A-Za-z0-9]{2}[0-9]{7}"

CHUNK = 500


def extract_ma_ref(note):
    match = MA_REF_RE.search((note or "").upper())
    return match.group() if match else None


def _chunks(items, size=CHUNK):
    items = list(items)
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _parts_doc_filter():
    q = Q()
    for b in BaseBranchCompany.objects.exclude(invoice_code__isnull=True).exclude(
        invoice_code=""
    ).select_related("affiliated"):
        if b.affiliated:
            q |= Q(comcod=b.affiliated.name, docnum__startswith=b.invoice_code)
    return q


def fetch_issue_docs(start_date, end_date):
    """หัวใบจ่ายอะไหล่ที่ note3 มีเลขใบแจ้งซ่อม -> [{docnum, comcod, docdat, note3}]"""
    doc_filter = _parts_doc_filter()
    if not doc_filter:
        return []
    return list(
        ExOESTNH.objects.using("pg_db")
        .filter(doc_filter, docdat__range=(start_date, end_date), note3__regex=MA_REF_SQL)
        .values("docnum", "comcod", "docdat", "note3")
    )


def fetch_issue_lines(docs):
    """รายการในใบ -> {(docnum, comcod): [line]} (docnum ซ้ำกันได้ข้ามบริษัท จึงจับคู่ทั้งสองค่า)"""
    keys = {(d["docnum"], d["comcod"]) for d in docs}
    lines = defaultdict(list)
    for chunk in _chunks({docnum for docnum, _ in keys}):
        rows = (
            ExOESTND.objects.using("pg_db")
            .filter(docnum__in=chunk, comcod__in={comcod for _, comcod in keys})
            .order_by("docnum", "seqnum")
            .values("docnum", "comcod", "stkcod", "stktyp", "ordqty", "unitnam", "trnval")
        )
        for row in rows:
            key = (row["docnum"], row["comcod"])
            if key in keys:
                lines[key].append(row)
    return lines


def fetch_express_names(stkcods):
    """ชื่อสินค้าจากรายการสินค้าของ Express (ICGOODS.stkth) -> {(STKCOD, comcod): ชื่อ}

    ICGOODS แยกตามบริษัท ชื่ออาจต่างกันเล็กน้อยในแต่ละบริษัท
    """
    names = {}
    with connections["pg_db"].cursor() as cur:
        for chunk in _chunks(stkcods):
            cur.execute(
                'SELECT TRIM(stkcod), TRIM(comcod), stkth FROM "ICGOODS" WHERE TRIM(stkcod) IN %s',
                [tuple(chunk)],
            )
            for stkcod, comcod, name in cur.fetchall():
                if name and name.strip():
                    names[(stkcod.upper(), comcod)] = name.strip()
    return names


def _express_name(names, stkcod, comcod):
    """ชื่อของบริษัทที่จ่าย ถ้าไม่มีใช้ชื่อจากบริษัทอื่น"""
    key = stkcod.upper()
    return names.get((key, comcod.strip())) or next(
        (name for (code, _), name in sorted(names.items()) if code == key), ""
    )


def collect_parts(ref_nos, start_date, end_date):
    """{ref_no ใบแจ้งซ่อม: [อะไหล่]} หรือ None ถ้าต่อ Express ไม่ได้

    None ต่างจาก {} : None = ไม่รู้ (อย่าลบข้อมูลเดิม), {} = ไม่มีการเบิกอะไหล่
    """
    wanted = {ref.upper() for ref in ref_nos if ref}
    try:
        docs = [d for d in fetch_issue_docs(start_date, end_date) if extract_ma_ref(d["note3"]) in wanted]
        lines = fetch_issue_lines(docs)
    except (ConnectionDoesNotExist, DatabaseError):
        logger.exception("อ่านใบจ่ายอะไหล่จาก Express ไม่ได้")
        return None

    # รหัสสินค้าใช้ร่วมกันระหว่าง webstock กับ Express: ใช้ชื่อใน webstock ก่อน ไม่มีค่อยใช้ของ Express
    stkcods = {(row["stkcod"] or "").strip() for rows in lines.values() for row in rows} - {""}
    names = {}
    for chunk in _chunks(stkcods):
        names.update(
            (pid.upper(), (name or "").strip())
            for pid, name in Product.objects.filter(id__in=chunk).values_list("id", "name")
        )
    missing = {code for code in stkcods if not names.get(code.upper())}
    try:
        express_names = fetch_express_names(missing) if missing else {}
    except DatabaseError:
        logger.exception("อ่านชื่อสินค้าจาก Express ไม่ได้")
        express_names = {}

    result = defaultdict(list)
    for doc in docs:
        ref = extract_ma_ref(doc["note3"])
        for row in lines.get((doc["docnum"], doc["comcod"]), []):
            stkcod = (row["stkcod"] or "").strip()
            result[ref].append({
                "source": "IV",
                "received": True,
                "docnum": doc["docnum"].strip(),
                "docdat": doc["docdat"].isoformat() if doc["docdat"] else None,
                "stkcod": stkcod,
                "name": names.get(stkcod.upper()) or _express_name(express_names, stkcod, doc["comcod"]),
                "stktyp": (row["stktyp"] or "").strip(),
                "qty": float(row["ordqty"] or 0),
                "unit": (row["unitnam"] or "").strip(),
                "amount": float(row["trnval"] or 0),
            })
    return dict(result)


# BaseApproveStatus: อนุมัติ
PO_APPROVED = 2


def collect_po_parts(rq_ids):
    """{requisition id: [รายการในใบสั่งซื้อที่อนุมัติแล้ว]} ราคาก่อน VAT/ส่วนลดท้ายใบ"""
    result = defaultdict(list)
    rows = (
        PurchaseOrderItem.objects.filter(
            item__requisit_id__in=rq_ids,
            po__is_cancel=False,
            po__is_draft=False,
            po__approver_status_id=PO_APPROVED,
        )
        .order_by("po_id", "id")
        .values(
            "item__requisit_id", "po__ref_no", "po__created", "is_receive", "item__product_id",
            "item__product__name", "item__product_name", "description", "quantity", "unit__name",
            "price",
        )
    )
    for row in rows:
        result[row["item__requisit_id"]].append({
            "source": "PO",
            "received": bool(row["is_receive"]),
            "docnum": row["po__ref_no"] or "",
            "docdat": row["po__created"].isoformat() if row["po__created"] else None,
            "stkcod": row["item__product_id"] or "",
            "name": (
                row["item__product__name"] or row["item__product_name"] or row["description"] or ""
            ).strip(),
            "stktyp": "",
            "qty": float(row["quantity"] or 0),
            "unit": row["unit__name"] or "",
            "amount": float(row["price"] or 0),
        })
    return result
