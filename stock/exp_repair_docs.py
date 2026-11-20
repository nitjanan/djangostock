"""ใบจ่ายสินค้าภายใน-อะไหล่ (Express, pg_db) รายใบ สำหรับ dashboard

dashboard ใช้ใบแจ้งซ่อม (Maintenance) เป็นหลัก รถที่ไม่มีใบแจ้งซ่อมในช่วงที่ดู
จะนับการซ่อมจากใบจ่ายอะไหล่แทน:
- remark = รถ (ชื่อ:รหัส) และ note3 = เลขที่ใบแจ้งซ่อม (ใช้หารถก่อน remark เหมือน getapiExpRepairAll)
- note2 = ประเภทการซ่อม (BaseRepairType.id)
- note1 = ชื่อผู้เบิก/ช่าง
ยอดเงินไม่รวมน้ำมัน (stkcod ขึ้นต้น OL) เหมือน getapiExpRepairAll
แต่ละใบมีรายการอะไหล่ (parts) ด้วย: dashboard ใช้ทำตารางอะไหล่ที่ใช้มากที่สุดของรถที่ไม่มีใบแจ้งซ่อม
"""
import logging
from collections import defaultdict

from django.db import DatabaseError, connections

from .car_match import build_car_maps
from .exp_car import maintenance_cars, resolve_exp_car
from .maintenance_parts import _chunks, extract_ma_ref, fetch_express_names
from .models import BaseBranchCompany, BaseCar, BaseRepairType, Product

logger = logging.getLogger(__name__)

SQL = """
    SELECT
        TRIM(nh.docnum) AS docnum,
        nh.docdat,
        TRIM(nh.remark) AS remark,
        TRIM(nh.note1) AS note1,
        TRIM(nh.note2) AS note2,
        TRIM(nh.note3) AS note3,
        SUM(CASE WHEN nd.stkcod NOT LIKE 'OL%%' THEN nd.trnval ELSE 0 END) AS amount
    FROM "OESTNH" nh
    JOIN "OESTND" nd
        ON nd.docnum = nh.docnum
        AND nd.comcod = nh.comcod
    WHERE
        nh.comcod = %s
        AND nh.docnum LIKE %s
        AND nh.docdat BETWEEN %s AND %s
    GROUP BY nh.docnum, nh.docdat, nh.remark, nh.note1, nh.note2, nh.note3
    ORDER BY nh.docdat, nh.docnum
"""

COLUMNS = ("docnum", "docdat", "remark", "note1", "note2", "note3", "amount")

# รายการในใบ (ไม่รวมน้ำมัน) เงื่อนไขเดียวกับ SQL
LINES_SQL = """
    SELECT
        TRIM(nd.docnum) AS docnum,
        TRIM(nd.stkcod) AS stkcod,
        TRIM(nd.stktyp) AS stktyp,
        nd.ordqty,
        TRIM(nd.unitnam) AS unitnam,
        nd.trnval
    FROM "OESTNH" nh
    JOIN "OESTND" nd
        ON nd.docnum = nh.docnum
        AND nd.comcod = nh.comcod
    WHERE
        nh.comcod = %s
        AND nh.docnum LIKE %s
        AND nh.docdat BETWEEN %s AND %s
        AND nd.stkcod NOT LIKE 'OL%%'
    ORDER BY nd.docnum, nd.seqnum
"""

LINE_COLUMNS = ("docnum", "stkcod", "stktyp", "qty", "unit", "amount")


def query_docs(b_com, start_date, end_date):
    """ใบจ่ายอะไหล่ของบริษัทเดียว: list ของ dict ตาม COLUMNS + lines (รายการในใบ)"""
    if not b_com.invoice_code or not b_com.affiliated:
        return []
    params = [b_com.affiliated.name, f"{b_com.invoice_code}%", start_date, end_date]
    with connections["pg_db"].cursor() as cursor:
        cursor.execute(SQL, params)
        docs = [dict(zip(COLUMNS, row)) for row in cursor.fetchall()]
        cursor.execute(LINES_SQL, params)
        lines = defaultdict(list)
        for row in cursor.fetchall():
            line = dict(zip(LINE_COLUMNS, row))
            lines[line["docnum"]].append(line)
    for doc in docs:
        doc["lines"] = lines.get(doc["docnum"], [])
        doc["comcod"] = b_com.affiliated.name
    return docs


def part_names(stkcods):
    """ชื่ออะไหล่: ใช้ชื่อใน webstock ก่อน ไม่มีค่อยใช้ของ Express (เหมือน collect_parts)

    คืน {STKCOD: ชื่อ webstock}, {(STKCOD, comcod): ชื่อ Express}
    """
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
    return names, express_names


class PartNamer:
    """เลือกชื่ออะไหล่ (ชื่อ Express ของบริษัทที่จ่ายก่อน ไม่มีใช้ของบริษัทอื่น เหมือน _express_name)"""

    def __init__(self, names=None, express_names=None):
        self.names = names or {}
        self.express_names = express_names or {}
        self.any_company = {}
        for (code, _), name in sorted(self.express_names.items()):
            self.any_company.setdefault(code, name)

    def __call__(self, stkcod, comcod):
        key = stkcod.upper()
        return (
            self.names.get(key)
            or self.express_names.get((key, comcod.strip()))
            or self.any_company.get(key, "")
        )


def doc_parts(doc, namer):
    return [
        {
            "stkcod": line["stkcod"] or "",
            "name": namer(line["stkcod"] or "", doc.get("comcod") or ""),
            "stktyp": line["stktyp"] or "",
            "qty": float(line["qty"] or 0),
            "unit": line["unit"] or "",
            "amount": float(line["amount"] or 0),
        }
        for line in doc.get("lines") or []
    ]


def build_doc_rows(
    docs_by_company, ma_cars, name_map, code_map, repair_names=None, namer=None
):
    """แปลงใบจ่ายเป็นแถวของ API (ทิ้งใบที่จับคู่รถไม่ได้: dashboard แสดงในแท็บ "อื่นๆ" อยู่แล้ว)

    docs_by_company: [(branch_company_id, [doc, ...]), ...]
    repair_names: {BaseRepairType.id: ชื่อ} เช่น "41" -> "PM" (dashboard ใช้แยกงาน PM ออกจากการซ่อม)
    """
    repair_names = repair_names or {}
    namer = namer or PartNamer()
    rows = []
    for branch_company_id, docs in docs_by_company:
        for doc in docs:
            car = resolve_exp_car(doc["remark"], doc["note3"], ma_cars, name_map, code_map)
            if not car:
                continue
            rows.append({
                "docnum": doc["docnum"],
                "docdat": doc["docdat"].isoformat(),
                "branch_company": branch_company_id,
                "car_id": car["id"],
                "car_dep": car["car_dep"],
                "remark": doc["remark"] or "",
                "requester": " ".join((doc["note1"] or "").split()),  # note1 มักมี NBSP คั่นชื่อ
                "repair_type": doc["note2"] or None,
                "repair_name": repair_names.get(doc["note2"] or ""),
                # เลขที่ใบแจ้งซ่อม (ตัดข้อความอื่นที่คีย์ปนมา) ไม่มี = None
                "ma_ref": extract_ma_ref(doc["note3"]),
                "amount": float(doc["amount"] or 0),
                "parts": doc_parts(doc, namer),
            })
    return rows


def collect_repair_docs(start_date, end_date):
    companies = BaseBranchCompany.objects.exclude(code="ALL").select_related("affiliated")
    docs_by_company = [(b.id, query_docs(b, start_date, end_date)) for b in companies]
    name_map, code_map = build_car_maps([
        {"id": c["id"], "name": c["name"], "code": (c["code"] or "").strip(), "car_dep": c["car_dep"]}
        for c in BaseCar.objects.values("id", "name", "code", "car_dep")
    ])
    ma_cars = maintenance_cars(d["note3"] for _, docs in docs_by_company for d in docs)
    repair_names = {str(rt.id): rt.name for rt in BaseRepairType.objects.all()}
    stkcods = {
        line["stkcod"] for _, docs in docs_by_company for d in docs for line in d["lines"]
    } - {"", None}
    return build_doc_rows(
        docs_by_company, ma_cars, name_map, code_map, repair_names, PartNamer(*part_names(stkcods))
    )
