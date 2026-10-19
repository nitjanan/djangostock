"""ตรวจจับการคีย์บันทึกการใช้รถ (CarLogbook) ที่ผิดปกติ สำหรับแสดงในหน้า /carLogBook/"""
import datetime

from django.db.models import OuterRef, Q, Subquery

from .models import CarLogbook

MAX_DAILY_DISTANCE = 500  # ระยะทางต่อใบเกินนี้ถือว่าผิดปกติ (กม.)
MAX_GAP = 50  # ไมล์เริ่มกระโดดจากไมล์สิ้นสุดใบก่อนหน้าเกินนี้ถือว่าผิดปกติ (กม.)
MAX_JOB_HOURS = 16  # เวลางานเดียวเกินนี้น่าจะคีย์เวลาผิด
DEFAULT_DAYS = 30  # ถ้าไม่ได้เลือกวันที่ ตรวจย้อนหลังกี่วัน

MILE_JOBS = range(1, 7)
TIME_JOBS = range(1, 5)


def _fmt(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _minutes(t):
    return t.hour * 60 + t.minute


def _mile_issues(cl):
    """คืน list ของ (ข้อความ, ชื่อ field ที่ผิด)"""
    issues = []
    if cl.mile_start is not None and cl.mile_end is not None:
        if cl.mile_end < cl.mile_start:
            issues.append((f"ไมล์สิ้นสุด ({_fmt(cl.mile_end)}) น้อยกว่าไมล์เริ่ม ({_fmt(cl.mile_start)})",
                           {"mile_start", "mile_end"}))
        elif cl.mile_end - cl.mile_start > MAX_DAILY_DISTANCE:
            issues.append((f"ระยะทาง {_fmt(cl.mile_end - cl.mile_start)} กม. เกิน {MAX_DAILY_DISTANCE} กม.",
                           {"mile_start", "mile_end"}))

    prev_n, prev_end = None, None
    for n in MILE_JOBS:
        start = getattr(cl, f"mile_start_job{n}")
        end = getattr(cl, f"mile_end_job{n}")
        if start is not None and end is not None and end < start:
            issues.append((f"งานที่ {n}: ไมล์สิ้นสุด ({_fmt(end)}) น้อยกว่าไมล์เริ่ม ({_fmt(start)})",
                           {f"mile_start_job{n}", f"mile_end_job{n}"}))
        if start is not None and prev_end is not None and start < prev_end:
            issues.append((f"งานที่ {n}: ไมล์เริ่ม ({_fmt(start)}) น้อยกว่าไมล์สิ้นสุดงานที่ {prev_n} ({_fmt(prev_end)})",
                           {f"mile_start_job{n}", f"mile_end_job{prev_n}"}))
        if end is not None:
            prev_n, prev_end = n, end
    return issues


def _prev_issues(cl, prev):
    """คืน list ของ (ข้อความ, field ที่ผิดของใบนี้, field ที่ผิดของใบก่อนหน้า)"""
    if cl.mile_start is None or prev is None:
        return []
    prev_end = prev.mile_end
    if cl.mile_start < prev_end:
        return [(f"ไมล์เริ่ม ({_fmt(cl.mile_start)}) น้อยกว่าไมล์สิ้นสุด ({_fmt(prev_end)}) ของใบก่อนหน้า",
                 {"mile_start"}, {"mile_end"})]
    if cl.mile_start - prev_end > MAX_GAP:
        return [(f"ไมล์เริ่ม ({_fmt(cl.mile_start)}) ห่างจากไมล์สิ้นสุด ({_fmt(prev_end)}) ของใบก่อนหน้า เกิน {MAX_GAP} กม.",
                 {"mile_start"}, {"mile_end"})]
    return []


def _time_issues(cl):
    """คืน list ของ (ข้อความ, ชื่อ field ที่ผิด) โดย time_jobN หมายถึงเวลาเริ่ม-สิ้นสุดงานที่ N"""
    issues = []
    spans = []
    for n in TIME_JOBS:
        start = getattr(cl, f"start_job{n}")
        end = getattr(cl, f"end_job{n}")
        if start is None or end is None:
            continue
        s, e = _minutes(start), _minutes(end)
        if e < s:  # ข้ามวัน (เหมือน calculateDiffTime)
            e += 24 * 60
        if e - s > MAX_JOB_HOURS * 60:
            issues.append((f"งานที่ {n}: เวลา {start:%H:%M}-{end:%H:%M} นานเกิน {MAX_JOB_HOURS} ชม.",
                           {f"time_job{n}"}))
        spans.append((n, s, e))

    for i, (n1, s1, e1) in enumerate(spans):
        for n2, s2, e2 in spans[i + 1:]:
            if s1 < e2 and s2 < e1:
                issues.append((f"เวลางานที่ {n1} และงานที่ {n2} ซ้อนทับกัน", {f"time_job{n1}", f"time_job{n2}"}))
    return issues


def job_rows(cl, bad_fields):
    """แถวงานที่มีข้อมูล สำหรับแสดงใน chain-panel พร้อมธงว่าช่องไหนผิด"""
    rows = []
    for n in MILE_JOBS:
        row = {
            "n": n,
            "job": getattr(cl, f"job{n}"),
            "mile_start": getattr(cl, f"mile_start_job{n}"),
            "mile_end": getattr(cl, f"mile_end_job{n}"),
            "start": getattr(cl, f"start_job{n}", None),
            "end": getattr(cl, f"end_job{n}", None),
            "bad_mile_start": f"mile_start_job{n}" in bad_fields,
            "bad_mile_end": f"mile_end_job{n}" in bad_fields,
            "bad_time": f"time_job{n}" in bad_fields,
        }
        if any(row[k] is not None for k in ("job", "mile_start", "mile_end", "start", "end")):
            rows.append(row)
    return rows


def default_scope(queryset, has_date):
    """ไม่นับใบที่ยกเลิก และถ้าไม่ได้เลือกวันที่ ตรวจเฉพาะ DEFAULT_DAYS วันล่าสุด"""
    queryset = queryset.filter(is_cancel=False)
    if not has_date:
        since = datetime.date.today() - datetime.timedelta(days=DEFAULT_DAYS)
        queryset = queryset.filter(created__gte=since)
    return queryset


def detect_carlog_anomalies(queryset, visible=None):
    """คืน list เฉพาะใบที่มีความผิดปกติ แต่ละรายการเป็น
    {'cl', 'issues': [{'text', 'prev'}], 'bad_fields', 'jobs', 'prev', 'prev_bad_fields', 'prev_jobs'}
    โดย bad_fields คือชื่อ field ที่ผิด ใช้ไฮไลต์ใน chain-panel
    visible คือ queryset ใบที่ user มีสิทธิ์เห็น ใช้จำกัดการหาใบก่อนหน้า (รถคันเดียวกันอาจอยู่หลายบริษัท)"""
    if visible is None:
        visible = CarLogbook.objects.all()
    # ใบก่อนหน้าของรถคันเดียวกัน (ไม่นับใบยกเลิก) เรียงตามวันที่แล้วตาม id
    prev = visible.filter(
        car=OuterRef("car"), is_cancel=False, mile_end__isnull=False,
    ).filter(
        Q(created__lt=OuterRef("created")) | Q(created=OuterRef("created"), id__lt=OuterRef("id"))
    ).order_by("-created", "-id")

    cls = list(queryset.annotate(prev_cl_id=Subquery(prev.values("id")[:1])))
    prev_ids = {cl.prev_cl_id for cl in cls if cl.car_id and cl.prev_cl_id}
    prevs = visible.select_related("branch_company", "name").in_bulk(prev_ids)

    result = []
    for cl in cls:
        prev_cl = prevs.get(cl.prev_cl_id) if cl.car_id else None
        issues, bad_fields, prev_bad_fields = [], set(), set()
        for text, fields in _mile_issues(cl):
            issues.append({"text": text, "prev": None})
            bad_fields |= fields
        for text, fields, prev_fields in _prev_issues(cl, prev_cl):
            issues.append({"text": text, "prev": prev_cl})
            bad_fields |= fields
            prev_bad_fields |= prev_fields
        for text, fields in _time_issues(cl):
            issues.append({"text": text, "prev": None})
            bad_fields |= fields
        if issues:
            result.append({
                "cl": cl,
                "issues": issues,
                "bad_fields": bad_fields,
                "jobs": job_rows(cl, bad_fields),
                "prev": prev_cl,
                "prev_bad_fields": prev_bad_fields,
                "prev_jobs": job_rows(prev_cl, set()) if prev_cl else [],
            })
    return result
