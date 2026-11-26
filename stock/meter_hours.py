"""ชั่วโมงทำงานจากหน้าปัดชั่วโมง (เครื่องจักร) ของบันทึกการใช้รถ คิดทีละรายการแล้วรวม

เดิม getapiExpWorkByMonthAll คิดชั่วโมงของเดือน = เลขไมล์สิ้นสุดรายการสุดท้าย - เลขไมล์เริ่มรายการแรก
หน้าปัดชั่วโมงมีทศนิยม 1 ตำแหน่ง คนกรอกบางวันใส่จุด (642 -> 653 = 11 ชม.) บางวันไม่ใส่
(6532 -> 6646 = 11.4 ชม.) เลขต้น-ท้ายเดือนจึงคนละหลัก ได้ชั่วโมงเป็นพัน หรือติดลบเป็นแสน

คิดทีละรายการแทน:
- ผลต่าง 0-24 = ชั่วโมงตามที่กรอก
- ผลต่างเกิน 24 แต่หาร 10 แล้วไม่เกิน 24 = กรอกไม่มีจุดทศนิยม -> หาร 10
- ติดลบ หรือเกิน 240 = กรอกผิด ไม่นับรายการนั้น (รายการอื่นของเดือนยังนับ)

ใช้กับแผนกที่ใช้หน้าปัดชั่วโมงเท่านั้น (รถที่เป็นเลขไมล์ กม. ต่อวันเกิน 24 ได้จริง)
"""
from collections import defaultdict
from decimal import Decimal

MAX_HOURS_PER_DAY = Decimal(24)
TENTHS = Decimal(10)


def entry_hours(mile_start, mile_end):
    """ชั่วโมงของบันทึก 1 รายการ (None = เลขไม่ครบหรือกรอกผิด ไม่นับ)"""
    if mile_start is None or mile_end is None:
        return None
    diff = Decimal(mile_end) - Decimal(mile_start)
    if diff < 0:
        return None
    if diff <= MAX_HOURS_PER_DAY:
        return diff
    if diff / TENTHS <= MAX_HOURS_PER_DAY:
        return diff / TENTHS
    return None


def meter_hours_by_car_month(logbooks):
    """{(car_id, "ปี-เดือน"): ชั่วโมงรวม} จาก queryset ที่มี year_month (ดู getapiExpWorkByMonthAll)"""
    hours = defaultdict(Decimal)
    for row in logbooks.values("car", "year_month", "mile_start", "mile_end"):
        h = entry_hours(row["mile_start"], row["mile_end"])
        if h is not None:
            hours[(row["car"], row["year_month"])] += h
    return hours
