"""สรุปงานจากบันทึกการใช้รถ (CarLogbook) ให้ fleet dashboard

ใบบันทึกการใช้รถ 1 ใบมีได้ถึง 6 งาน แต่ละงานมีรายละเอียดงาน (jobN), เลขไมล์เริ่ม/จบ (diff_mile_jobN)
งานที่ 1-4 มีเวลาเริ่ม/จบ (diff_time_jobN) และแผนกค่าใช้จ่าย (exd_jobN) ด้วย

ผลลัพธ์รวมเป็นแถวละ (เดือน, บริษัท, รถ, แผนกค่าใช้จ่าย, รายละเอียดงาน):
ชั่วโมงทำงาน = ผลรวมเวลางาน, ระยะทาง = ผลรวมเลขไมล์ของงาน, จำนวนเที่ยว = จำนวนงาน
ไม่นับใบที่ยกเลิก (is_cancel) และใบที่ไม่ได้ระบุรถ
"""

from collections import defaultdict
from datetime import datetime

from stock.models import CarLogbook

JOB_SLOTS = range(1, 7)
TIMED_SLOTS = range(1, 5)  # งานที่ 1-4 มีเวลาเริ่ม/จบและแผนกค่าใช้จ่าย


def _fields():
    fields = ["created", "car_id", "car__car_dep_id", "branch_company_id"]
    for n in JOB_SLOTS:
        fields += [f"job{n}", f"diff_mile_job{n}"]
    for n in TIMED_SLOTS:
        fields += [f"diff_time_job{n}", f"exd_job{n}_id", f"exd_job{n}__name"]
    return fields


def _jobs(row):
    """งานที่กรอกไว้ในใบเดียว: (แผนกค่าใช้จ่าย, ชื่อแผนก, รายละเอียดงาน, ชั่วโมง, กม.)"""
    for n in JOB_SLOTS:
        timed = n in TIMED_SLOTS
        job = (row[f"job{n}"] or "").strip()
        duration = row[f"diff_time_job{n}"] if timed else None
        km = row[f"diff_mile_job{n}"]
        if not job and not duration and not km:
            continue
        hours = duration.total_seconds() / 3600 if duration else 0.0
        yield (
            row[f"exd_job{n}_id"] if timed else None,
            row[f"exd_job{n}__name"] if timed else None,
            job,
            hours,
            float(km) if km and km > 0 else 0.0,
        )


def collect_carlog_jobs(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    rows = (
        CarLogbook.objects.filter(
            created__gte=start, created__lte=end, is_cancel=False, car__isnull=False
        )
        .values(*_fields())
        .order_by("created", "id")
    )

    groups = defaultdict(lambda: {"hours": 0.0, "km": 0.0, "trips": 0, "days": set()})
    meta = {}
    for row in rows:
        created = row["created"]
        for exd_id, exd_name, job, hours, km in _jobs(row):
            key = (
                created.year,
                created.month,
                row["branch_company_id"],
                row["car_id"],
                exd_id,
                job,
            )
            g = groups[key]
            g["hours"] += hours
            g["km"] += km
            g["trips"] += 1
            g["days"].add(created)
            meta[key] = (row["car__car_dep_id"], exd_name)

    result = []
    for key, g in groups.items():
        year, month, company_id, car_id, exd_id, job = key
        car_dep_id, exd_name = meta[key]
        result.append(
            {
                "year": year,
                "month": month,
                "branch_company": company_id,
                "car_id": car_id,
                "car_dep": car_dep_id,
                "expense_dept_id": exd_id,
                "expense_dept_name": exd_name,
                "job": job,
                "hours": round(g["hours"], 2),
                "km": round(g["km"], 2),
                "trips": g["trips"],
                "days": len(g["days"]),
            }
        )
    result.sort(key=lambda r: (r["year"], r["month"], str(r["branch_company"]), r["car_id"]))
    return result
