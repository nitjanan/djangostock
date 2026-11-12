"""ค่าแนะนำสำหรับช่องกรองข้อความในหน้ารายการ (viewxxx)

ค่าแนะนำมาจาก "เอกสารที่หน้านั้นแสดง" เท่านั้น (สถานะ/บริษัทเดียวกับตาราง) เลือกแล้วกดกรองจึงเจอเสมอ
- filters.py: ช่องที่มีค่าแนะนำใช้ widget=SuggestInput('<path>') — path คือ field ของค่า นับจาก model ของ FilterSet
- view: หลังสร้าง myFilter ให้เรียก
      suggest = filter_suggest_response(request, myFilter, rejected_qs)
      if suggest: return suggest
  (ส่ง queryset ของแท็บอื่นในหน้าเดียวกันเพิ่มได้ เช่น แท็บไม่อนุมัติ)
- _text_filter_suggest.html: dropdown เรียก URL ของหน้าเดิม ?_suggest=<ชื่อช่อง>&q=<คำค้น>
"""
from django.db.models import Max
from django.forms.widgets import TextInput
from django.http import JsonResponse

from .thai_search import text_similar_q, user_name_q

SUGGEST_LIMIT = 20
SUGGEST_PARAM = '_suggest'
NOTE_TEXT_LIMIT = 120


class SuggestInput(TextInput):
    """ช่องกรองข้อความที่มี dropdown ค่าที่เคยบันทึก

    path:   field ของค่าที่แนะนำ นับจาก model ของ FilterSet (หรือจาก model ที่ source คืนมา)
    label:  field ที่แสดงต่อท้าย (เช่น รหัสสินค้า + ชื่อ) ค้นได้ทั้งสองอย่าง แต่ค่าที่ส่งไปกรองเป็น path
    kind:   'text' | 'user' (path ชี้ไปที่ User แนะนำ "ชื่อ นามสกุล") | 'note' (ข้อความยาว/หลายบรรทัด)
    source: ฟังก์ชัน queryset ของหน้า -> queryset ของ model อื่น เมื่อไม่มี relation ให้ join ตรงๆ
    """

    def __init__(self, path, label=None, kind='text', source=None, attrs=None):
        super().__init__(attrs=dict(attrs or {}, **{'data-suggest': kind}))
        self.suggest_path = path
        self.suggest_label = label
        self.suggest_kind = kind
        self.suggest_source = source


def _shorten(text, limit):
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + '…'


def _first_line(text):
    #browser แปลงตัวขึ้นบรรทัดตอนส่งฟอร์ม (\n -> \r\n) ข้อความหลายบรรทัดจึงกรองไม่เจอ ใช้บรรทัดแรกแทน (กรองแบบ "มีคำนี้")
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ''


def _suggest_from(qs, widget, term):
    """คืน (ค่าที่ส่งไปกรอง, {ค่า: ข้อความที่แสดง})"""
    path = widget.suggest_path
    qs = qs.order_by()

    if widget.suggest_kind == 'user':
        rows = (qs.filter(user_name_q(path + '__', term))
                .values_list(path + '__first_name', path + '__last_name')
                .distinct()[:SUGGEST_LIMIT])
        return [('%s %s' % (f or '', l or '')).strip() for f, l in rows], {}

    qs = qs.exclude(**{path + '__isnull': True}).exclude(**{path: ''})
    label = widget.suggest_label
    #มี label ค้นได้ทั้งจากรหัสหรือชื่อ
    match = text_similar_q(path, term)
    if label:
        match |= text_similar_q(label, term)
    qs = qs.filter(match)

    if label:
        rows = list(qs.values_list(path, label).distinct().order_by(path)[:SUGGEST_LIMIT])
        return [v for v, _ in rows], {v: '%s  %s' % (v, l or '') for v, l in rows}
    #ค่าที่ใช้ล่าสุดขึ้นก่อน (ไม่ซ้ำกัน)
    rows = qs.values(path).annotate(last=Max('pk')).order_by('-last')[:SUGGEST_LIMIT]
    values = [r[path] for r in rows]
    if widget.suggest_kind == 'note':
        labels = {}
        for v in values:
            labels.setdefault(_first_line(v), _shorten(v, NOTE_TEXT_LIMIT))
        return [_first_line(v) for v in values], labels
    return values, {}


def filter_suggest_response(request, filterset, *extra_querysets):
    """ตอบ JSON ค่าแนะนำ (รูปแบบ select2) ถ้า request มี ?_suggest=<ชื่อช่อง> ไม่งั้นคืน None

    ค่ามาจาก filterset.queryset (เอกสารที่หน้านี้แสดง ก่อนกรอง) และ extra_querysets (แท็บอื่นของหน้าเดียวกัน)"""
    name = request.GET.get(SUGGEST_PARAM)
    if not name:
        return None
    flt = filterset.filters.get(name)
    widget = flt.extra.get('widget') if flt is not None else None
    if not isinstance(widget, SuggestInput):
        return JsonResponse({'results': []}, status=404)
    term = (request.GET.get('q') or '').strip()

    results, seen = [], set()
    if term:
        for qs in (filterset.queryset,) + extra_querysets:
            if widget.suggest_source:
                qs = widget.suggest_source(qs)
            values, labels = _suggest_from(qs, widget, term)
            for v in values:
                if v and v not in seen and len(results) < SUGGEST_LIMIT:
                    seen.add(v)
                    results.append({'id': v, 'text': labels.get(v, v)})
    return JsonResponse({'results': results})
