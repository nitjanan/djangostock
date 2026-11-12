"""ค้นหาภาษาไทยแบบสะกดคล้ายกัน ใช้ร่วมกันทั้ง views (ช่องค้นหาสินค้า / ผู้จำหน่าย) และ filters (ชื่อผู้ใช้)
เช่น พิมพ์ "สาย" เจอ "ศาย", "สต็อก" เจอ "สต็อค"/"สตอก", "สรี" เจอ "ศรี"
หน้าเว็บใช้กฎชุดเดียวกันผ่าน {% thai_similar_rules %} (templatehelpers) — แก้กลุ่มตัวอักษรที่นี่ที่เดียว"""
import re

from django.db.models import Q

#พยัญชนะต้นเสียงเดียวกัน
THAI_SIMILAR_GROUPS = [
    'สศษซ', 'ทธฑฒถฐ', 'ตฏ', 'ดฎ', 'กคฆฅฃข', 'พภผ', 'ฟฝ',
    'นณ', 'ลฬ', 'ชฌฉ', 'ยญ', 'หฮ', 'ไใ',
]
#ตัวสะกด (ท้ายพยางค์) เสียงเดียวกัน: แม่กก / แม่กด / แม่กบ
THAI_FINAL_GROUPS = ['กขคฆ', 'ดจชซฎฏฐฑฒตถทธศษส', 'บปพฟภ']
THAI_MARKS = '่้๊๋็'  #วรรณยุกต์ + ไม้ไต่คู้: มีหรือไม่มีก็ค้นเจอ
THAI_LEADING_VOWELS = 'เแโใไ'  #ตัวที่ตามหลังสระหน้าเป็นพยัญชนะต้น ไม่ใช่ตัวสะกด เช่น ฟ ใน "ไฟ"
THAI_BEFORE_FINAL = 'ะัาำิีึืุู' + THAI_MARKS + 'อว'  #ตัวที่มักอยู่ก่อนตัวสะกด

_SIMILAR_MAP = {c: g for g in THAI_SIMILAR_GROUPS for c in g}
_FINAL_MAP = {c: g for g in THAI_FINAL_GROUPS for c in g}
_MARKS_OPT = '(' + '|'.join(THAI_MARKS) + ')*'


def _is_thai(c):
    return '฀' <= c <= '๿'


def _is_thai_consonant(c):
    return 'ก' <= c <= 'ฮ'


def thai_similar_pattern(word):
    """regex ที่ให้ตัวอักษรเสียงเดียวกันแทนกันได้ หรือ None ถ้าคำนี้ไม่มีตัวอักษรไทย
    ตัวสะกด (ตัวท้ายคำ หรือมีสระ/วรรณยุกต์นำหน้าแล้วตามด้วยพยัญชนะ) ใช้กลุ่มเสียงตัวสะกดแทน
    ใช้แบบ (ส|ศ|ษ|ซ) แทน [สศษซ] เพื่อให้ใช้ได้ทั้ง MySQL (แม้ regex แบบ byte) และ JavaScript"""
    if not any(_is_thai(c) for c in word):
        return None
    chars = [c for c in word if c not in THAI_MARKS]
    parts = []
    for i, c in enumerate(chars):
        if not _is_thai(c):
            parts.append(re.escape(c))
            continue
        prev = chars[i - 1] if i > 0 else ''
        nxt = chars[i + 1] if i + 1 < len(chars) else ''
        is_final = (i > 0 and c in _FINAL_MAP and prev not in THAI_LEADING_VOWELS
                    and (not nxt or (_is_thai_consonant(nxt) and prev in THAI_BEFORE_FINAL)))
        group = _FINAL_MAP[c] if is_final else _SIMILAR_MAP.get(c)
        parts.append(('(' + '|'.join(group) + ')' if group else c) + _MARKS_OPT)
    return ''.join(parts) or None


def text_similar_q(field, value):
    """เงื่อนไขค้นหาข้อความ (เช่น ชื่อผู้จำหน่าย): ทุกคำที่พิมพ์ต้องเจอใน field (สะกดคล้ายก็เจอ)
    เช่น field='distributor__name' พิมพ์ "สรี พาณิช" เจอ "ศรีพานิช" """
    q = Q()
    for word in (value or '').split():
        cond = Q(**{field + '__icontains': word})
        pattern = thai_similar_pattern(word)
        if pattern:
            cond |= Q(**{field + '__iregex': pattern})
        q &= cond
    return q


def user_name_q(prefix, value):
    """เงื่อนไขค้นหาผู้ใช้จากชื่อ/นามสกุล: ทุกคำที่พิมพ์ต้องเจอในชื่อหรือนามสกุล (สะกดคล้ายก็เจอ)
    prefix คือ path ไปยัง User เช่น 'name__' หรือ 'requisition__name__'
    เช่น "สมชาย ใจดี" / "ใจดี" / "สมชาย" / "ศมชาย" เจอ สมชาย ใจดี"""
    q = Q()
    for word in (value or '').split():
        cond = Q(**{prefix + 'first_name__icontains': word}) | Q(**{prefix + 'last_name__icontains': word})
        pattern = thai_similar_pattern(word)
        if pattern:
            cond |= Q(**{prefix + 'first_name__iregex': pattern}) | Q(**{prefix + 'last_name__iregex': pattern})
        q &= cond
    return q
