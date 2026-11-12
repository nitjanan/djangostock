from django import template
import datetime
from django.utils.timezone import get_current_timezone, is_naive, localtime, make_aware

register = template.Library()

@register.simple_tag
def my_url(value, field_name, urlencode=None):
    url = '?{}={}'.format(field_name, value)
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, None)

@register.filter
def format_datetime(value):
    if isinstance(value, datetime.datetime):
        if is_naive(value):
            value = make_aware(value, get_current_timezone())
        return localtime(value).strftime("%d/%m/%Y %H:%M")
    return value

@register.filter
def first_chars(value, num=2):
    return value[:num] if value else ''

@register.filter
def get_localtime(value):
    if isinstance(value, datetime.datetime):
        if is_naive(value):
            value = make_aware(value, get_current_timezone())
        if value.time() == datetime.time(0, 0, 0):
            return localtime(value)
        return localtime(value)
    return value

@register.filter
def bound_field(form, name):
    """ดึง field ของฟอร์มด้วยชื่อแบบไดนามิก เช่น {{ form|bound_field:"job1" }}"""
    return form[name]


# ===== ใบบันทึกการใช้รถ: ชั่วโมงงาน / ระยะทาง (ใช้ในหน้ารายการ /carLogBook/ และ /report/carLogBook/) =====
def _to_minutes(t):
    if t is None or t == '':
        return None
    if isinstance(t, (datetime.time, datetime.datetime)):
        return t.hour * 60 + t.minute
    try:
        h, m = str(t).split(':')[:2]
        return int(h) * 60 + int(m)
    except (ValueError, TypeError):
        return None


def _fmt_hm(minutes):
    return '%d:%02d' % (minutes // 60, minutes % 60)


def _to_num(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


@register.simple_tag
def cl_job_hours(start, end):
    """ชั่วโมงของงาน 1 งาน -> {'text': 'H:MM', 'bad': bool} หรือ None ถ้าข้อมูลไม่ครบ"""
    s, e = _to_minutes(start), _to_minutes(end)
    if s is None or e is None:
        return None
    if e < s:
        return {'text': 'เวลาผิด', 'bad': True}
    return {'text': _fmt_hm(e - s), 'bad': False}


@register.simple_tag
def cl_job_dist(ms, me):
    """ระยะทางของงาน 1 งาน -> {'value': float, 'bad': bool} หรือ None"""
    s, e = _to_num(ms), _to_num(me)
    if s is None or e is None:
        return None
    return {'value': e - s, 'bad': e < s}


@register.simple_tag
def cl_summary(cl):
    """สรุปทั้งใบ แบบเดียวกับหน้าแก้ไข:
    - ชั่วโมงงานรวม = ผลรวมเวลางานที่ 1-4 (editCL)
    - ระยะทาง = ผลรวมระยะแต่ละเที่ยว ถ้ามีไมล์รายเที่ยว (ร้อยเกาะ) ไม่งั้นใช้ ไมล์สิ้นสุด - ไมล์เริ่ม
    """
    total_min, any_time = 0, False
    for i in range(1, 5):
        s = _to_minutes(getattr(cl, 'start_job%d' % i, None))
        e = _to_minutes(getattr(cl, 'end_job%d' % i, None))
        if s is not None and e is not None and e >= s:
            total_min += e - s
            any_time = True

    trip_total, trips, trip_bad = 0.0, 0, False
    for i in range(1, 7):
        s = _to_num(getattr(cl, 'mile_start_job%d' % i, None))
        e = _to_num(getattr(cl, 'mile_end_job%d' % i, None))
        if s is None or e is None:
            continue
        if e < s:
            trip_bad = True
            continue
        trip_total += e - s
        trips += 1

    dist, dist_bad = None, False
    if trips or trip_bad:
        dist, dist_bad = trip_total, trip_bad
    else:
        ms, me = _to_num(cl.mile_start), _to_num(cl.mile_end)
        if ms is not None and me is not None:
            dist, dist_bad = me - ms, me < ms

    return {
        'hours': _fmt_hm(total_min) if any_time else None,
        'dist': dist,
        'dist_bad': dist_bad,
        'trips': trips,
    }

@register.simple_tag
def thai_similar_rules():
    #กฎค้นหาไทยแบบสะกดคล้าย (stock/thai_search.py) ส่งให้ JavaScript ใช้ชุดเดียวกับฝั่ง server
    import json
    from django.utils.safestring import mark_safe
    from stock import thai_search as ts
    return mark_safe(json.dumps({
        'groups': ts.THAI_SIMILAR_GROUPS,
        'finals': ts.THAI_FINAL_GROUPS,
        'marks': ts.THAI_MARKS,
        'leading': ts.THAI_LEADING_VOWELS,
        'beforeFinal': ts.THAI_BEFORE_FINAL,
    }, ensure_ascii=False))
