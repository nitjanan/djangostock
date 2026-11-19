"""ค่าซ่อม/น้ำมันในโปรแกรมบัญชี Express ที่ remark จับคู่กับ BaseCar ไม่ได้ (ยังไม่ได้ตั้งค่ารถ)

ใช้ทั้ง API ที่ dashboard ดึง (getapiExpUnmatchedAll) และหน้า admin "รายการที่ยังไม่ได้ตั้งค่า" ของ BaseCar
"""
import re
from collections import defaultdict

from .car_match import build_car_maps, clean_remark, resolve_car
from .exp_car import maintenance_cars, resolve_exp_car
from .models import BaseBranchCompany, BaseCar


def collect_unmatched(start_date, end_date):
    """คืน list ของ dict ต่อ (บริษัท, ปี, เดือน, remark): repair_amount, oil_qty

    query Express (pg_db) ทุกบริษัท ใช้กติกาจับคู่เดียวกับ API ค่าซ่อม/น้ำมัน
    """
    # import ตอนเรียก: views.py ใหญ่มากและ import admin ไม่ควรโหลดทั้งไฟล์
    from .views import query_exp_oil_by_month_all, query_exp_repair_all

    branch_companies = list(
        BaseBranchCompany.objects.exclude(code='ALL').select_related('affiliated')
    )
    name_map, code_map = build_car_maps(list(BaseCar.objects.values('id', 'name', 'code')))

    totals = defaultdict(lambda: {'repair_amount': 0.0, 'oil_qty': 0.0})

    repairs = [
        (b_com, query_exp_repair_all(start_date, end_date, b_com))
        for b_com in branch_companies
    ]
    # ค่าซ่อม: note3 ชี้ใบแจ้งซ่อมที่มีรถ = จับคู่ได้ แม้ remark ผิด (เหมือน getapiExpRepairAll)
    ma_cars = maintenance_cars(item['note3'] for _, data in repairs for item in data)

    for b_com, data in repairs:

        for item in data:
            amount = float(item['sum_amount'] or 0)
            if amount and not resolve_exp_car(
                item['car_code'], item['note3'], ma_cars, name_map, code_map
            ):
                key = (b_com.id, item['year'], item['month'], clean_remark(item['car_code']))
                totals[key]['repair_amount'] += amount

        for item in query_exp_oil_by_month_all(start_date, end_date, b_com):
            qty = float(item['sum_qty'] or 0)
            if qty and not resolve_car(item['remark'], name_map, code_map):
                key = (b_com.id, item['year'], item['month'], clean_remark(item['remark']))
                totals[key]['oil_qty'] += qty

    return [
        {
            'branch_company': branch_company,
            'year': year,
            'month': month,
            'remark': remark,
            'repair_amount': round(values['repair_amount'], 2),
            'oil_qty': round(values['oil_qty'], 2),
        }
        for (branch_company, year, month, remark), values in sorted(totals.items())
    ]


def summarize_by_remark(rows):
    """รวมทุกเดือนเป็นแถวเดียวต่อ (บริษัท, remark) เรียงค่าซ่อมมากไปน้อย"""
    grouped = {}
    for row in rows:
        key = (row['branch_company'], row['remark'])
        item = grouped.setdefault(key, {
            'branch_company': row['branch_company'],
            'remark': row['remark'],
            'repair_amount': 0.0,
            'oil_qty': 0.0,
            'months': set(),
        })
        item['repair_amount'] += row['repair_amount']
        item['oil_qty'] += row['oil_qty']
        item['months'].add(f"{row['year']}-{row['month']}")

    result = []
    for item in grouped.values():
        item['month_count'] = len(item.pop('months'))
        item['repair_amount'] = round(item['repair_amount'], 2)
        item['oil_qty'] = round(item['oil_qty'], 2)
        result.append(item)
    result.sort(key=lambda r: (-r['repair_amount'], -r['oil_qty'], r['remark']))
    return result


def suggest_car(remark):
    """ค่าเริ่มต้นของฟอร์มเพิ่มรถจาก remark: (name, code)

    'โรงโม่1:TM1' -> ('โรงโม่1', 'TM1'), 'SY375H(J2)' -> ('SY375H', 'J2'), 'ZX210LC' -> ('ZX210LC', '')
    """
    text = clean_remark(remark)
    code = ''
    if ':' in text:
        text, after = text.split(':', 1)
        words = after.split()
        code = words[0] if words else ''
    inner = re.findall(r'\(([^)]*)\)', text)
    if inner and not code:
        code = inner[0].strip()
    name = re.sub(r'\([^)]*\)', ' ', text)
    name = re.sub(r'\s+', ' ', name).strip()
    # ข้อความในวงเล็บที่ไม่ใช่รหัส (เช่น 'รถน้ำ') ไม่ต้องเติมให้
    if code and not re.fullmatch(r'[A-Za-z0-9\-]{1,20}', code):
        code = ''
    return name, code
