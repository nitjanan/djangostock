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

    # ----- สถานะในตารางผู้จัดจำหน่ายอื่นๆ -----

    def status_of(self, shop):
        vendors = [dict(shop)]
        _annotate_system_status(vendors, "osm")
        return vendors[0]

    def test_status_new_draft_pending_in_system(self):
        self.assertEqual(self.status_of(OSM_SHOP)["system_status"], "new")
        self.propose()
        self.assertEqual(self.status_of(OSM_SHOP)["system_status"], "draft")
        c = DistributorCandidate.objects.get()
        self.fill_form(c, action="submit")
        self.assertEqual(self.status_of(OSM_SHOP)["system_status"], "pending")
        self.approve(c, mode="new", distributor_id="V001")
        ev = self.status_of(OSM_SHOP)
        self.assertEqual((ev["system_status"], ev["distributor_id"]), ("in_system", "V001"))

    def test_osm_way_and_node_with_same_number_are_different_places(self):
        Distributor.objects.create(id="V001", name="x", place_source="osm", place_id="way/555")
        self.assertEqual(self.status_of(OSM_SHOP)["system_status"], "new")

    # ----- ยื่นฟอร์ม -----

    def test_propose_creates_draft_and_opens_form(self):
        response = self.propose()
        c = DistributorCandidate.objects.get()
        self.assertRedirects(response, reverse('distributorCandidateForm', args=[c.pk]), fetch_redirect_response=False)
        self.assertEqual(c.status, DistributorCandidate.STATUS_DRAFT)
        self.assertEqual(c.requested_by, self.user)
        self.assertEqual(c.latitude, Decimal("13.756331"))
        # กดซ้ำ -> กลับไปฟอร์มเดิม ไม่สร้างใบใหม่
        self.propose()
        self.assertEqual(DistributorCandidate.objects.count(), 1)

    def test_other_user_cannot_edit_draft(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        response = self.propose(user=self.other)
        self.assertRedirects(response, reverse('distributorCandidateDetail', args=[c.pk]), fetch_redirect_response=False)
        self.login(self.other)
        self.client.post(reverse('distributorCandidateForm', args=[c.pk]), {"action": "save", "name": "แก้ชื่อ"})
        c.refresh_from_db()
        self.assertEqual(c.name, OSM_SHOP["name"])

    def test_save_draft_stores_header_and_answers(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.fill_form(c, answers={"3": "fail"}, contact="คุณสมชาย", tax_id="0105555000000", credit_days="30")
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_DRAFT)
        self.assertEqual((c.contact, c.tax_id, c.credit_days), ("คุณสมชาย", "0105555000000", 30))
        self.assertEqual(c.answers.count(), len(LEAF_CODES))
        self.assertEqual(c.answers.get(question=self.rules["3"]).ans, "fail")

    def test_parent_rule_cannot_be_answered(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.login(self.user)
        self.client.post(reverse('distributorCandidateForm', args=[c.pk]), {
            "action": "save", "name": c.name, f"ans_{self.rules['9'].pk}": "pass",
        })
        self.assertFalse(c.answers.filter(question=self.rules["9"]).exists())

    def test_submit_requires_all_answers(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.fill_form(c, action="submit", skip=("5",))
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_DRAFT)

        self.fill_form(c, action="submit")
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_SUBMITTED)
        self.assertIsNotNone(c.submitted_at)

    def test_cancel_draft_deletes_it(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.login(self.user)
        self.client.post(reverse('distributorCandidateForm', args=[c.pk]), {"action": "cancel"})
        self.assertFalse(DistributorCandidate.objects.exists())

    # ----- อนุมัติ -----

    def test_approve_new_copies_form_into_distributor(self):
        c = self.submitted_candidate(contact="คุณสมชาย", fax_line="@line", tax_id="0105555000000")
        self.approve(c, mode="new", distributor_id="V900")

        d = Distributor.objects.get(id="V900")
        self.assertEqual((d.name, d.address, d.tel), (OSM_SHOP["name"], OSM_SHOP["address"], OSM_SHOP["phone"]))
        self.assertEqual((d.contact, d.fax, d.tex), ("คุณสมชาย", "@line", "0105555000000"))
        self.assertEqual((d.place_source, d.place_id), ("osm", "node/555"))
        self.assertEqual((d.latitude, d.longitude), (Decimal("13.756331"), Decimal("100.501765")))
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_APPROVED)
        self.assertEqual((c.distributor, c.approved_by), (d, self.approver))
        self.assertIsNotNone(c.approved_at)

    def test_approve_new_requires_vat_type(self):
        # ตาราง Distributor จริงตั้ง vat_type_id เป็น NOT NULL
        c = self.submitted_candidate()
        self.approve(c, mode="new", distributor_id="V900", vat_type="")
        self.assertFalse(Distributor.objects.filter(id="V900").exists())

        self.approve(c, mode="new", distributor_id="V900", vat_type=self.vat.pk)
        self.assertEqual(Distributor.objects.get(id="V900").vat_type, self.vat)

    def test_cannot_approve_when_mandatory_fails(self):
        c = self.submitted_candidate(answers={"2": "fail"})
        self.assertEqual(c.status, DistributorCandidate.STATUS_SUBMITTED)
        self.approve(c, mode="new", distributor_id="V900")
        self.assertFalse(Distributor.objects.filter(id="V900").exists())
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_SUBMITTED)

    def test_cannot_approve_draft(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.fill_form(c)
        self.approve(c, mode="new", distributor_id="V900")
        self.assertFalse(Distributor.objects.filter(id="V900").exists())

    def test_approve_new_rejects_existing_express_id(self):
        Distributor.objects.create(id="V900", name="ร้านอื่น")
        c = self.submitted_candidate()
        self.approve(c, mode="new", distributor_id="V900")
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_SUBMITTED)
        self.assertIsNone(Distributor.objects.get(id="V900").place_id)

    def test_approve_link_accepts_autocomplete_value_with_dash_in_id(self):
        Distributor.objects.create(id="D-01", name="เจริญการช่าง")
        c = self.submitted_candidate()
        self.approve(c, mode="link", distributor_id="D-01-เจริญการช่าง")
        d = Distributor.objects.get(id="D-01")
        self.assertEqual(d.place_id, "node/555")
        self.assertEqual(d.name, "เจริญการช่าง")  # ผูกรายเดิม ไม่ทับข้อมูลเดิม
        self.assertEqual(Distributor.objects.count(), 1)

    def test_user_outside_group_cannot_approve_or_reject(self):
        c = self.submitted_candidate()
        self.approve(c, user=self.user, mode="new", distributor_id="V900")
        self.login(self.user)
        self.client.post(reverse('rejectDistributorCandidate', args=[c.pk]))
        self.assertFalse(Distributor.objects.filter(id="V900").exists())
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_SUBMITTED)

    def test_rejected_can_be_proposed_again_keeping_answers(self):
        c = self.submitted_candidate(answers={"3": "fail"})
        self.login(self.approver)
        self.client.post(reverse('rejectDistributorCandidate', args=[c.pk]), {"reject_reason": "ราคาสูง"})
        c.refresh_from_db()
        self.assertEqual((c.status, c.reject_reason, c.approved_by), (DistributorCandidate.STATUS_REJECTED, "ราคาสูง", self.approver))

        self.propose(user=self.other)
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_DRAFT)
        self.assertEqual(c.requested_by, self.other)
        self.assertIsNone(c.approved_by)
        self.assertIsNone(c.reject_reason)
        self.assertEqual(c.answers.get(question=self.rules["3"]).ans, "fail")

    def test_propose_redirect_ignores_external_next(self):
        Distributor.objects.create(id="V001", name="x", place_source="osm", place_id="node/555")
        response = self.propose(next="https://evil.example.com/")
        self.assertEqual(response.url, reverse('viewVendorReport'))

    # ----- หน้าจอ -----

    @patch("stock.views.fetch_vendors_from_openstreetmap")
    def test_report_filters_by_system_status(self, fetch):
        other = dict(OSM_SHOP, name="ร้านในระบบ", osm_id=777)
        fetch.side_effect = lambda *a, **k: [dict(OSM_SHOP), dict(other)]
        Distributor.objects.create(id="V777", name="ร้านในระบบ", place_source="osm", place_id="node/777")

        self.login(self.user)
        url = reverse('viewVendorReport') + "?lat=13.75&lng=100.5&source=osm"
        response = self.client.get(url + "&system_status=new")
        self.assertEqual([ev["name"] for ev in response.context["external_vendors"]], [OSM_SHOP["name"]])
        self.assertContains(response, "เสนอเพิ่ม")

        response = self.client.get(url + "&system_status=in_system")
        self.assertEqual([ev["distributor_id"] for ev in response.context["external_vendors"]], ["V777"])
        self.assertContains(response, "มีในระบบ: V777")

    @patch("stock.views.fetch_vendors_from_tomtom")
    @patch("stock.views.fetch_vendors_from_openstreetmap")
    def test_report_lists_saved_candidates_without_map_search(self, fetch_osm, fetch_tomtom):
        self.propose()
        draft = DistributorCandidate.objects.get()
        approved = DistributorCandidate.objects.create(place_source="osm", place_id="node/9", name="ร้านอนุมัติแล้ว", status="approved")

        self.login(self.user)
        response = self.client.get(reverse('viewVendorReport'))
        fetch_osm.assert_not_called()
        fetch_tomtom.assert_not_called()
        self.assertEqual([c.pk for c in response.context["candidates"]], [draft.pk])
        self.assertContains(response, reverse('distributorCandidateForm', args=[draft.pk]))

        response = self.client.get(reverse('viewVendorReport') + "?cand_status=approved")
        self.assertEqual([c.pk for c in response.context["candidates"]], [approved.pk])

    @patch("stock.views.fetch_vendors_from_openstreetmap", return_value=[])
    def test_report_region_presets(self, fetch):
        self.login(self.user)
        response = self.client.get(reverse('viewVendorReport'))
        self.assertContains(response, 'data-lat="9.138200" data-lng="99.321700"')
        self.assertIsNone(response.context["region"])

        # ภาคที่เลือกค้างไว้ในหน้า + ค้นตามพิกัดของภาคนั้น
        response = self.client.get(reverse('viewVendorReport') + "?region=south&lat=9.138200&lng=99.321700&source=osm")
        self.assertEqual(response.context["region"], "south")
        self.assertContains(response, '<option value="south" data-lat="9.138200" data-lng="99.321700" selected>', html=False)
        self.assertEqual(fetch.call_args[0][:2], (9.1382, 99.3217))

        # ค่าที่ไม่รู้จักถูกตัดทิ้ง
        response = self.client.get(reverse('viewVendorReport') + "?region=mars")
        self.assertIsNone(response.context["region"])

    def test_form_page_renders_rules(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.login(self.user)
        response = self.client.get(reverse('distributorCandidateForm', args=[c.pk]))
        self.assertContains(response, "ความถูกต้องทางกฎหมาย")
        self.assertContains(response, f'name="ans_{self.rules["9.1"].pk}"')
        self.assertNotContains(response, f'name="ans_{self.rules["9"].pk}"')

    def test_requester_detail_page_is_read_only_even_for_approver(self):
        c = self.submitted_candidate()
        for user in (self.user, self.approver):
            self.login(user)
            response = self.client.get(reverse('distributorCandidateDetail', args=[c.pk]))
            self.assertContains(response, OSM_SHOP["name"])
            self.assertContains(response, "สรุป: ผ่านเกณฑ์บังคับ")
            self.assertNotContains(response, "อนุมัติ + สร้างใหม่")

    def test_approve_pages_only_for_group(self):
        c = self.submitted_candidate(answers={"1": "fail"})
        self.login(self.approver)
        response = self.client.get(reverse('distributorApproveList'))
        self.assertEqual([x.pk for x in response.context["candidates"]], [c.pk])
        self.assertContains(response, "ไม่ผ่าน")
        self.assertContains(response, "ข้อ 1 ความถูกต้องทางกฎหมาย")
        response = self.client.get(reverse('distributorApproveDetail', args=[c.pk]))
        self.assertContains(response, "อนุมัติ + สร้างใหม่")
        self.assertContains(response, "ชนิดภาษี")

        self.login(self.user)
        for url in (reverse('distributorApproveList'), reverse('distributorApproveDetail', args=[c.pk])):
            self.assertRedirects(self.client.get(url), reverse('viewVendorReport'), fetch_redirect_response=False)

    def test_approve_returns_to_queue(self):
        c = self.submitted_candidate()
        response = self.approve(c, mode="new", distributor_id="V900")
        self.assertRedirects(response, reverse('distributorApproveList'), fetch_redirect_response=False)

    def test_report_page_shows_approve_button_only_for_approver(self):
        self.submitted_candidate()
        self.login(self.approver)
        response = self.client.get(reverse('viewVendorReport'))
        self.assertEqual(response.context["dist_ap_count"], 1)
        self.assertContains(response, reverse('distributorApproveList'))

        self.login(self.user)
        response = self.client.get(reverse('viewVendorReport'))
        self.assertNotIn("dist_ap_count", response.context)
        self.assertNotContains(response, reverse('distributorApproveList'))

    def test_print_page_shows_signers_and_supplier_code(self):
        c = self.submitted_candidate()
        self.approve(c, mode="new", distributor_id="V900")
        self.login(self.user)
        response = self.client.get(reverse('distributorCandidatePrint', args=[c.pk]))
        self.assertContains(response, "FM-PU-005 Rev.01")
        self.assertContains(response, "V900")
        self.assertContains(response, "requester")
        self.assertContains(response, "approver")

    def test_pages_render_when_users_deleted(self):
        # ผู้ใช้ถูกลบ -> requested_by / approved_by เป็น NULL หน้าเว็บต้องไม่พัง
        c = self.submitted_candidate()
        self.approve(c, mode="new", distributor_id="V900")
        DistributorCandidate.objects.filter(pk=c.pk).update(requested_by=None, approved_by=None)
        self.login(self.approver)
        for name in ('distributorCandidateDetail', 'distributorApproveDetail', 'distributorCandidatePrint'):
            self.assertEqual(self.client.get(reverse(name, args=[c.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('distributorApproveList') + "?status=approved").status_code, 200)
        self.assertEqual(self.client.get(reverse('viewVendorReport') + "?cand_status=approved").status_code, 200)
