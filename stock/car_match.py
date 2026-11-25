"""จับคู่ remark ในเอกสารโปรแกรมบัญชี Express (pg_db) กับ BaseCar

remark คีย์มือ รูปแบบไม่ตรงกับ BaseCar เสมอ เช่น
    ภบ2100 / ภบ-2100 / ภบ 2100      -> ทะเบียน ภบ-2100
    9กฬ-5586 กทม.                    -> มีจังหวัดต่อท้าย
    ผข8465:TT1                       -> หลัง ':' คือ code
    โรงโม่5:SM5 Terex fix 5          -> code ตามด้วยคำอธิบาย
    SY375H(J2), 82-0178(MT29)        -> code อยู่ในวงเล็บ

ใช้ร่วมกันทุก API ที่ dashboard ดึง (ค่าซ่อม, น้ำมัน, รายการรถตามแผนก) ให้จับคู่ได้ผลเดียวกัน
"""
import re

# ตัวอักษรที่มักพิมพ์ผิด
THAI_SIMILAR = {
    'ฏ': 'ฎ',
}

# ทะเบียนรถไทย: 1กฬ-4965, ภบ 2100, กท3833 หรือป้ายรถบรรทุก 82-0178
# ต้องไม่ต่อท้ายคำอื่น กันไม่ให้ 'วัตถุระเบิดกงตาก1' กลายเป็นทะเบียน 'ตาก1'
PLATE_RE = re.compile(
    r'(?<![ก-๙A-Za-z0-9])(\d?\s*[ก-ฮ]{2,3})\s*-?\s*(\d{1,4})(?!\d)'
    r'|(?<![ก-๙A-Za-z0-9])(\d{2})\s*-\s*(\d{4})(?!\d)'
)


def normalize_text(txt):
    """ตัวพิมพ์ใหญ่ ตัดทุกอย่างที่ไม่ใช่ ไทย อังกฤษ ตัวเลข (ช่องว่าง, -, ., ฯลฯ)"""
    if not txt:
        return ''

    txt = str(txt).upper().strip().replace('\xa0', ' ')

    for old, new in THAI_SIMILAR.items():
        txt = txt.replace(old, new)

    return re.sub(r'[^A-Z0-9ก-๙]', '', txt)


def plate_keys(text):
    """ทะเบียนรถที่อยู่ในข้อความ (normalize แล้ว) เช่น '9กฬ-5586 กทม.' -> ['9กฬ5586']"""
    keys = []
    for m in PLATE_RE.finditer(str(text or '').replace('\xa0', ' ')):
        if m.group(1):
            keys.append(normalize_text(m.group(1) + m.group(2)))
        else:
            keys.append(m.group(3) + m.group(4))
    return [k for k in keys if k]


def remark_candidates(remark):
    """คีย์ที่จะลองเทียบ เรียงจากชัดที่สุดไปหลวมที่สุด: list ของ (ชนิด, ค่า)

    ชนิด 'code' เทียบกับ BaseCar.code, 'name' เทียบกับ BaseCar.name, 'any' เทียบทั้งสองอย่าง
    ถ้ามี ':' ใช้เฉพาะ code (หลัง ':' และในวงเล็บ) ไม่ย้อนไปเทียบชื่อหน้า ':'
    เพื่อไม่ให้ค่าใช้จ่ายไปลงผิดคันเมื่อ code ยังไม่ได้ตั้งใน BaseCar
    """
    raw = str(remark or '').replace('\xa0', ' ').strip()
    if not raw:
        return []

    out = []

    if ':' in raw:
        after = raw.split(':')[-1].strip()
        out.append(('code', normalize_text(after)))
        words = after.split()
        if words:
            out.append(('code', normalize_text(words[0])))  # 'SM5 Terex fix 5' -> SM5
        for inner in re.findall(r'\(([^)]*)\)', after):
            out.append(('code', normalize_text(inner)))
    else:
        for inner in re.findall(r'\(([^)]*)\)', raw):
            out.append(('code', normalize_text(inner)))  # 'SY375H(J2)' -> J2
        out.append(('any', normalize_text(raw)))
        outer = re.sub(r'\([^)]*\)', ' ', raw)
        out.append(('any', normalize_text(outer)))
        for key in plate_keys(raw):
            out.append(('name', key))

    seen = set()
    result = []
    for kind, value in out:
        if value and (kind, value) not in seen:
            seen.add((kind, value))
            result.append((kind, value))
    return result


def build_car_maps(cars):
    """cars: iterable ของ dict ที่มี 'name' และ 'code' (key อื่นติดไปกับผลลัพธ์)

    คืน (name_map, code_map) key เป็นค่าที่ normalize แล้ว
    name_map มีทั้งชื่อเต็มและทะเบียนในชื่อ ('9กฬ-5586 กทม.' -> '9กฬ5586กทม' และ '9กฬ5586')
    ชื่อที่ซ้ำกันหลายคัน (เช่น 'รถจีน' 5 คัน) ไม่ใส่ใน name_map เพราะบอกไม่ได้ว่าคันไหน
    ต้องคีย์ code ใน remark แทน
    """
    name_map = {}
    code_map = {}
    ambiguous = set()

    for car in cars:
        code = normalize_text(car.get('code'))
        if code:
            code_map.setdefault(code, car)

        name = normalize_text(car.get('name'))
        if name and code:
            code_map.setdefault(name + code, car)  # remark = ชื่อ+code ติดกัน เช่น ผข8465TT1
        if name:
            for key in {name, *plate_keys(car.get('name'))}:
                other = name_map.get(key)
                if other is not None and other is not car:
                    ambiguous.add(key)
                name_map[key] = car

    for key in ambiguous:
        del name_map[key]

    return name_map, code_map


def resolve_car(remark, name_map, code_map):
    """คืน dict ของรถที่ตรงกับ remark หรือ None ถ้าจับคู่ไม่ได้"""
    for kind, value in remark_candidates(remark):
        if kind in ('code', 'any') and value in code_map:
            return code_map[value]
        if kind in ('name', 'any') and value in name_map:
            return name_map[value]
    return None


def clean_remark(remark):
    """remark สำหรับแสดงผล: ตัด non-breaking space และช่องว่างซ้ำ"""
    return re.sub(r'\s+', ' ', str(remark or '').replace('\xa0', ' ')).strip()
