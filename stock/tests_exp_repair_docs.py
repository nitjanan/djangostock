from datetime import date

from django.test import SimpleTestCase

from stock.car_match import build_car_maps
from stock.exp_repair_docs import PartNamer, build_doc_rows


def doc(docnum, remark, note3="", note2="13", note1="สมชาย\xa0ใจดี", amount=100):
    return {
        "docnum": docnum, "docdat": date(2026, 6, 5), "remark": remark,
        "note1": note1, "note2": note2, "note3": note3, "amount": amount,
    }


class BuildDocRowsTest(SimpleTestCase):
    def setUp(self):
        self.name_map, self.code_map = build_car_maps([
            {"id": 1, "name": "ตฆ-551 ชบ", "code": "J6", "car_dep": 3},
            {"id": 2, "name": "ภบ-2100", "code": "T1", "car_dep": 2},
        ])

    def test_matches_car_by_remark_and_cleans_fields(self):
        rows = build_doc_rows(
            [("10", [doc("OU1", "ตฆ551ชบ:J6", note3="ใบ MJ16906039 ")])], {}, self.name_map, self.code_map,
            {"13": "ระบบส่งกำลัง"},
        )
        self.assertEqual(rows, [{
            "docnum": "OU1", "docdat": "2026-06-05", "branch_company": "10", "car_id": 1, "car_dep": 3,
            "remark": "ตฆ551ชบ:J6", "requester": "สมชาย ใจดี", "repair_type": "13", "repair_name": "ระบบส่งกำลัง",
            "ma_ref": "MJ16906039", "amount": 100.0, "parts": [],
        }])

    def test_ticket_in_note3_wins_over_remark_and_unknown_car_is_dropped(self):
        ma_cars = {"MJ16906039": {"id": 2, "name": "ภบ-2100", "code": "T1", "car_dep": 2}}
        rows = build_doc_rows(
            [("10", [doc("OU1", "ตฆ551ชบ:J6", note3="MJ16906039"), doc("OU2", "ไม่มีรถคันนี้")])],
            ma_cars, self.name_map, self.code_map,
        )
        self.assertEqual([(r["docnum"], r["car_id"]) for r in rows], [("OU1", 2)])
        self.assertEqual(rows[0]["repair_type"], "13")

    def test_blank_notes_become_empty(self):
        rows = build_doc_rows(
            [("10", [doc("OU1", "ตฆ551ชบ:J6", note2="", note1=None, amount=None)])],
            {}, self.name_map, self.code_map,
        )
        self.assertEqual((rows[0]["repair_type"], rows[0]["requester"], rows[0]["ma_ref"], rows[0]["amount"]), (None, "", None, 0.0))
        self.assertIsNone(rows[0]["repair_name"])

    def test_parts_use_webstock_name_then_express_name_of_issuing_company(self):
        d = doc("OU1", "ตฆ551ชบ:J6")
        d["comcod"] = "บริษัท ก"
        d["lines"] = [
            {"docnum": "OU1", "stkcod": "P1", "stktyp": "1", "qty": 2, "unit": "ชิ้น", "amount": 80},
            {"docnum": "OU1", "stkcod": "p2", "stktyp": None, "qty": None, "unit": None, "amount": None},
            {"docnum": "OU1", "stkcod": "P3", "stktyp": "", "qty": 1, "unit": "ลิตร", "amount": 20},
        ]
        namer = PartNamer(
            {"P1": "ไส้กรอง"},
            {("P2", "บริษัท ข"): "สายพาน ข", ("P2", "บริษัท ก"): "สายพาน ก", ("P3", "บริษัท ข"): "จารบี"},
        )
        [row] = build_doc_rows([("10", [d])], {}, self.name_map, self.code_map, namer=namer)
        self.assertEqual(row["parts"], [
            {"stkcod": "P1", "name": "ไส้กรอง", "stktyp": "1", "qty": 2.0, "unit": "ชิ้น", "amount": 80.0},
            {"stkcod": "p2", "name": "สายพาน ก", "stktyp": "", "qty": 0.0, "unit": "", "amount": 0.0},
            {"stkcod": "P3", "name": "จารบี", "stktyp": "", "qty": 1.0, "unit": "ลิตร", "amount": 20.0},
        ])
