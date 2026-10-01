from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from stock.models import (
    BaseBranchCompany, BaseVatType, Distributor, DistributorCandidate, DistributorForm, DistributorRule,
    DistributorRuleGroup, UserProfile,
)
from stock.views import _annotate_system_status


OSM_SHOP = {
    "name": "ร้านเจริญการช่าง",
    "shop_type": "hardware",
    "address": "1 ถนนทดสอบ",
    "lat": 13.756331,
    "lng": 100.501765,
    "phone": "081-111-2222",
    "osm_id": 555,
    "osm_type": "node",
}

LEAF_CODES = ["1", "2", "3", "4", "5", "6", "7", "8", "9.1", "9.2", "10", "11"]


class DistributorCandidateTestCase(TestCase):
    """ร้านจากแผนที่ -> ผู้คัดเลือกกรอกใบ FM-PU-005 -> ส่ง -> กลุ่ม ApproveDistributor อนุมัติ -> เข้า Distributor"""

    def setUp(self):
        self.approver_group, _ = Group.objects.get_or_create(name='ApproveDistributor')
        self.user = User.objects.create_user(username='requester', password='password')
        self.other = User.objects.create_user(username='other', password='password')
        self.approver = User.objects.create_user(username='approver', password='password')
        self.approver.groups.add(self.approver_group)
        branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        for u in (self.user, self.other, self.approver):
            UserProfile.objects.create(user=u).branch_company.add(branch)
        self.rules = {r.code: r for r in DistributorRule.objects.all()}
        self.no_vat = BaseVatType.objects.create(id="0", name="ไม่มี vat")
        self.vat = BaseVatType.objects.create(id="1", name="รวม vat")

    def login(self, user):
        # RequireCompanyCodeMiddleware logout ทุกคนที่ session ไม่มี company_code
        self.client.force_login(user)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    def propose(self, user=None, **overrides):
        data = {
            "place_source": "osm",
            "place_id": "node/555",
            "name": OSM_SHOP["name"],
            "address": OSM_SHOP["address"],
            "tel": OSM_SHOP["phone"],
            "shop_type": "ร้านวัสดุ",
            "lat": "13.756331",
            "lng": "100.501765",
        }
        data.update(overrides)
        self.login(user or self.user)
        return self.client.post(reverse('proposeDistributorCandidate'), data)

    def fill_form(self, candidate, action="save", answers=None, skip=(), **header):
        """ตอบผ่านทุกข้อ ยกเว้นที่ระบุใน answers / ข้ามข้อใน skip"""
        # หน้าฟอร์มส่งค่าส่วนหัวที่กรอกไว้แล้วกลับมาทุกช่อง
        data = {"action": action}
        for field in ("name", "address", "branch", "contact", "tel", "fax_line", "tax_id", "email", "business_type"):
            data[field] = getattr(candidate, field) or ""
        data.update(header)
        answers = answers or {}
        for code in LEAF_CODES:
            if code not in skip:
                data[f"ans_{self.rules[code].pk}"] = answers.get(code, "pass")
        self.login(self.user)
        return self.client.post(reverse('distributorCandidateForm', args=[candidate.pk]), data)

    def submitted_candidate(self, answers=None, **header):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.fill_form(c, action="submit", answers=answers, **header)
        c.refresh_from_db()
        return c

    def approve(self, candidate, user=None, **data):
        if data.get("mode") == "new":
            data.setdefault("vat_type", self.no_vat.pk)
        self.login(user or self.approver)
        return self.client.post(reverse('approveDistributorCandidate', args=[candidate.pk]), data)

    # ----- หลักเกณฑ์จาก migration -----

    def test_rules_seeded_from_fm_pu_005(self):
        self.assertEqual(sorted(self.rules), sorted(LEAF_CODES + ["9"]))
        self.assertEqual(self.rules["9.1"].parent, self.rules["9"])
        self.assertEqual(DistributorRuleGroup.objects.count(), 4)
        self.assertEqual(self.rules["8"].mandatory_group, self.rules["9"].mandatory_group)
        self.assertIsNone(self.rules["3"].mandatory_group)

    # ----- ตรวจเกณฑ์บังคับ -----

    def evaluate_with(self, answers):
        c = DistributorCandidate.objects.create(place_source="osm", place_id=f"node/{DistributorCandidate.objects.count()}", name="x")
        for code in LEAF_CODES:
            DistributorForm.objects.create(candidate=c, question=self.rules[code], ans=answers.get(code, "pass"))
        return c.evaluate()

    def test_all_pass(self):
        e = self.evaluate_with({})
        self.assertTrue(e["mandatory_passed"])
        self.assertEqual(e["missing"], [])

    def test_mandatory_single_rule_fail(self):
        self.assertFalse(self.evaluate_with({"1": "fail"})["mandatory_passed"])
        # ข้อไม่บังคับไม่ผ่าน ไม่กระทบ
        self.assertTrue(self.evaluate_with({"3": "fail", "11": "fail"})["mandatory_passed"])

    def test_rule_8_or_9(self):
        self.assertTrue(self.evaluate_with({"8": "fail"})["mandatory_passed"])
        self.assertTrue(self.evaluate_with({"9.1": "fail", "9.2": "fail"})["mandatory_passed"])
        self.assertFalse(self.evaluate_with({"8": "fail", "9.1": "fail", "9.2": "fail"})["mandatory_passed"])

    def test_rule_9_children_mode(self):
        # ค่าเริ่มต้น all: 9.1 ไม่ผ่าน -> ข้อ 9 ไม่ผ่าน -> 8 ก็ไม่ผ่าน -> กลุ่มไม่ผ่าน
        self.assertFalse(self.evaluate_with({"8": "fail", "9.1": "fail"})["mandatory_passed"])
        DistributorRule.objects.filter(code="9").update(children_mode=DistributorRule.CHILDREN_ANY)
        self.assertTrue(self.evaluate_with({"8": "fail", "9.1": "fail"})["mandatory_passed"])

    def test_inactive_rule_not_required(self):
        DistributorRule.objects.filter(code="11").update(is_active=False)
        c = DistributorCandidate.objects.create(place_source="osm", place_id="node/1", name="x")
        for code in LEAF_CODES[:-1]:
            DistributorForm.objects.create(candidate=c, question=self.rules[code], ans="pass")
        e = c.evaluate()
        self.assertEqual(e["missing"], [])
        self.assertNotIn("11", [row["rule"].code for row in e["rows"]])
