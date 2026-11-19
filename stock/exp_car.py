"""หารถของใบจ่ายสินค้าภายในใน Express (pg_db) สำหรับค่าซ่อมต่อคัน

remark (ทะเบียนรถ) คีย์มือ พิมพ์ผิดแล้วค่าซ่อมไปลงผิดคันหรือจับคู่ไม่ได้
ถ้า note3 มีเลขใบแจ้งซ่อมที่มีอยู่จริง ใช้รถของใบแจ้งซ่อมนั้นแทน ไม่สน remark:

    1. note3 -> Maintenance.ref_no -> Maintenance.car
    2. ไม่มี note3 / หาใบแจ้งซ่อมไม่เจอ / ใบแจ้งซ่อมไม่มีรถ -> จับคู่ remark แบบเดิม (car_match.py)
    3. remark ก็จับคู่ไม่ได้ -> None (ไปอยู่ในรายการจับคู่ไม่ได้)

ใช้ร่วมกันระหว่าง getapiExpRepairAll และ collect_unmatched ให้ผลตรงกัน
"""
from .car_match import resolve_car
from .maintenance_parts import extract_ma_ref
from .models import Maintenance


def maintenance_cars(note3s):
    """{เลขใบแจ้งซ่อม: รถ} ของ note3 ที่มีเลขใบแจ้งซ่อม (รถ = dict รูปแบบเดียวกับ build_car_maps)"""
    refs = {ref for ref in (extract_ma_ref(n) for n in note3s) if ref}
    if not refs:
        return {}
    rows = (
        Maintenance.objects.filter(ref_no__in=refs, is_cancel=False, car__isnull=False)
        .order_by('id')
        .values('ref_no', 'car_id', 'car__name', 'car__code', 'car__car_dep')
    )
    cars = {}
    for r in rows:
        cars.setdefault(r['ref_no'].upper(), {
            'id': r['car_id'],
            'name': r['car__name'],
            'code': (r['car__code'] or '').strip(),
            'car_dep': r['car__car_dep'],
        })
    return cars


def resolve_exp_car(remark, note3, ma_cars, name_map, code_map):
    """รถของใบจ่าย: ใบแจ้งซ่อมใน note3 ก่อน ไม่เจอค่อยใช้ remark"""
    ref = extract_ma_ref(note3)
    if ref and ref in ma_cars:
        return ma_cars[ref]
    return resolve_car(remark, name_map, code_map)
