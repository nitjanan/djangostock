"""การจับคู่ remark จากโปรแกรมบัญชี Express กับ BaseCar (stock/car_match.py)"""
from django.test import SimpleTestCase

from .car_match import build_car_maps, clean_remark, plate_keys, resolve_car

CARS = [
    {'id': 1, 'name': 'ภบ-2100', 'code': 'PT6'},
    {'id': 2, 'name': '9กฬ-5586 กทม.', 'code': 'JT3'},
    {'id': 3, 'name': 'SY375', 'code': 'J2'},
    {'id': 4, 'name': 'โรงโม่5', 'code': 'SM5'},
    {'id': 5, 'name': '82-0178', 'code': 'MT29'},
    {'id': 6, 'name': 'โรงโม่1', 'code': 'SM1'},
    {'id': 7, 'name': 'รถจีน', 'code': 'J10'},
    {'id': 8, 'name': 'รถจีน', 'code': 'J11'},
    {'id': 9, 'name': 'ผข-8465', 'code': 'TT1'},
]


class CarMatchTestCase(SimpleTestCase):

    def setUp(self):
        self.name_map, self.code_map = build_car_maps(CARS)

    def match(self, remark):
        car = resolve_car(remark, self.name_map, self.code_map)
        return car and car['id']

    def test_plate_with_or_without_dash_or_space(self):
        for remark in ['ภบ2100', 'ภบ-2100', 'ภบ 2100', ' ภบ2100 ', 'ภบ\xa02100']:
            self.assertEqual(self.match(remark), 1, remark)

    def test_province_suffix(self):
        self.assertEqual(self.match('9กฬ-5586 กทม.'), 2)
        self.assertEqual(self.match('9กฬ5586'), 2)

    def test_code_after_colon_even_with_extra_words(self):
        self.assertEqual(self.match('ผข8465:TT1'), 9)
        self.assertEqual(self.match('โรงโม่5:SM5 Terex fix 5'), 4)

    def test_code_in_parentheses(self):
        self.assertEqual(self.match('SY375H(J2)'), 3)
        self.assertEqual(self.match('82-0178(MT29)'), 5)

    def test_name_and_code_joined(self):
        self.assertEqual(self.match('ผข8465TT1'), 9)

    def test_colon_with_unknown_code_does_not_fall_back_to_name(self):
        # TM1 ยังไม่ได้ตั้งใน BaseCar -> ต้องไม่เอาไปลง 'โรงโม่1' (SM1)
        self.assertIsNone(self.match('โรงโม่1:TM1'))

    def test_duplicate_name_is_ambiguous_but_code_still_matches(self):
        self.assertIsNone(self.match('รถจีน'))
        self.assertEqual(self.match('รถจีน:J11'), 8)

    def test_not_a_car(self):
        self.assertIsNone(self.match('ปุ๋ยแอมโมเนียมไนเตรท'))
        self.assertIsNone(self.match(''))
        self.assertIsNone(self.match(None))
        self.assertEqual(plate_keys('วัตถุระเบิดกงตาก1'), [])

    def test_plate_keys_and_clean_remark(self):
        self.assertEqual(plate_keys('รถยนต์นั่ง กษ-4111'), ['กษ4111'])
        self.assertEqual(plate_keys('82-0178(MT29)'), ['820178'])
        self.assertEqual(clean_remark(' งานซ่อม\xa0 โรงโม่ '), 'งานซ่อม โรงโม่')
