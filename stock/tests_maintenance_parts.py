import datetime
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from stock import maintenance_parts
from stock.maintenance_parts import collect_parts, extract_ma_ref
from stock.models import (
    BaseAddress,
    BaseBranchCompany,
    BaseCar,
    BranchCompanyBaseAdress,
    Category,
    Maintenance,
    Product,
)

START, END = "2026-01-01", "2026-11-30"


def doc(docnum, comcod, note3, docdat=datetime.date(2026, 10, 3)):
    return {"docnum": docnum + "   ", "comcod": comcod + "   ", "docdat": docdat, "note3": note3}


def line(docnum, comcod, stkcod, qty="1", amount="100.00", stktyp="อะไหล่", unit="ตัว"):
    return {
        "docnum": docnum + "   ", "comcod": comcod + "   ", "stkcod": stkcod + "  ",
        "stktyp": stktyp, "ordqty": Decimal(qty), "unitnam": unit, "trnval": Decimal(amount),
    }


class ExtractMaRefTestCase(TestCase):
    def test_finds_ref_in_free_text(self):
        self.assertEqual(extract_ma_ref("MR16910004"), "MR16910004")
        self.assertEqual(extract_ma_ref("ซ่อมตาม mr16910004 ด่วน"), "MR16910004")
        self.assertIsNone(extract_ma_ref("เลขไมล์ 44056"))
        self.assertIsNone(extract_ma_ref(None))


class CollectPartsTestCase(TestCase):
    """Express (pg_db) ต่อในเทสต์ไม่ได้ จึง mock ส่วนที่ query Express"""

    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="อะไหล่", slug="parts")
        Product.objects.create(id="HA-S0-226", name="ลูกปืนล้อ", slug="ha-s0-226", category=category)

    def _run(self, docs, lines, refs=("MR16910004",), express_names=None):
        with mock.patch.object(maintenance_parts, "fetch_issue_docs", return_value=docs), \
                mock.patch.object(maintenance_parts, "fetch_issue_lines", wraps=lambda d: _group(lines, d)), \
                mock.patch.object(maintenance_parts, "fetch_express_names",
                                  return_value=express_names or {}) as names:
            self.express_lookup = names
            return collect_parts(refs, START, END)

    def test_groups_lines_by_job_order_with_product_names(self):
        parts = self._run(
            [doc("OU6910019", "CTM", "MR16910004")],
            [line("OU6910019", "CTM", "HA-S0-226", qty="2", amount="2398.40"),
             line("OU6910019", "CTM", "XX-UNKNOWN"),
             line("OU6910019", "CTM", "XX-EXPRESS"),
             line("OU6910019", "CTM", "XX-OTHERCO")],
            express_names={("XX-EXPRESS", "CTM"): "กรองแอร์", ("XX-EXPRESS", "SLC"): "กรองแอร์ SLC",
                           ("XX-OTHERCO", "SLC"): "สายพาน"},
        )
        self.assertEqual(list(parts), ["MR16910004"])
        first, second, third, fourth = parts["MR16910004"]
        self.assertEqual(first, {
            "source": "IV", "received": True, "docnum": "OU6910019", "docdat": "2026-10-03", "stkcod": "HA-S0-226",
            "name": "ลูกปืนล้อ", "stktyp": "อะไหล่", "qty": 2.0, "unit": "ตัว", "amount": 2398.4,
        })
        self.assertEqual(second["name"], "")  # ไม่มีทั้ง 2 ระบบ แสดงรหัสแทน
        self.assertEqual(third["name"], "กรองแอร์")  # ไม่มีใน webstock ใช้ชื่อใน Express ของบริษัทที่จ่าย
        self.assertEqual(fourth["name"], "สายพาน")  # บริษัทที่จ่ายไม่มี ใช้ชื่อจากบริษัทอื่น
        # ถามชื่อจาก Express เฉพาะรหัสที่ webstock ไม่มี
        self.assertEqual(self.express_lookup.call_args.args[0], {"XX-UNKNOWN", "XX-EXPRESS", "XX-OTHERCO"})

    def test_ignores_docs_for_other_job_orders(self):
        parts = self._run(
            [doc("OU1", "CTM", "MR16910004"), doc("OU2", "CTM", "MR19999999")],
            [line("OU1", "CTM", "A"), line("OU2", "CTM", "B")],
        )
        self.assertEqual([p["stkcod"] for p in parts["MR16910004"]], ["A"])

    def test_same_docnum_in_other_company_is_not_mixed_in(self):
        parts = self._run(
            [doc("OU1", "CTM", "MR16910004")],
            [line("OU1", "CTM", "A"), line("OU1", "SLC", "B")],
        )
        self.assertEqual([p["stkcod"] for p in parts["MR16910004"]], ["A"])

    def test_returns_none_when_express_is_unreachable(self):
        with mock.patch.object(maintenance_parts, "fetch_issue_docs", side_effect=DatabaseError("down")):
            self.assertIsNone(collect_parts(["MR16910004"], START, END))


def _group(lines, docs):
    """แทน fetch_issue_lines: จับคู่ (docnum, comcod) แบบเดียวกับของจริง"""
    keys = {(d["docnum"], d["comcod"]) for d in docs}
    result = {}
    for row in lines:
        key = (row["docnum"], row["comcod"])
        if key in keys:
            result.setdefault(key, []).append(row)
    return result


class ProcessApiPartsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=branch, address=address)
        car = BaseCar.objects.create(id="1", name="รถ 1")
        cls.ma = Maintenance.objects.create(
            branch_company=branch, car=car, created=datetime.datetime(2026, 11, 3, 8),
            ref_no="MR16910004",
        )
        cls.user = User.objects.create_user(username="dashboard_api", password="pw")

    def _get(self):
        client = APIClient()
        client.force_authenticate(self.user)
        return client.get(reverse("getapiMaintenanceProcess", args=["2026-11-01", "2026-11-30"])).json()

    def test_parts_attached_to_job_order(self):
        part = {"stkcod": "A", "name": "ยาง"}
        with mock.patch("stock.maintenance_process.collect_parts", return_value={"MR16910004": [part]}):
            [row] = self._get()
        self.assertEqual(row["parts"], {"issued": [part], "purchased": []})

    def test_parts_none_when_express_unreachable(self):
        with mock.patch("stock.maintenance_process.collect_parts", return_value=None):
            [row] = self._get()
        self.assertIsNone(row["parts"]["issued"])

    def test_no_parts_issued_is_empty_list(self):
        with mock.patch("stock.maintenance_process.collect_parts", return_value={}):
            [row] = self._get()
        self.assertEqual(row["parts"], {"issued": [], "purchased": []})
