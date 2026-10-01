from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from stock.models import BaseBranchCompany, Distributor, DistributorCandidate, UserProfile
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


class DistributorCandidateTestCase(TestCase):
    """ร้านจากแผนที่ -> เสนอเพิ่ม -> กลุ่ม ApproveDistributor อนุมัติ -> เข้า Distributor พร้อม place_id / lat / lng"""

    def setUp(self):
        self.approver_group, _ = Group.objects.get_or_create(name='ApproveDistributor')
        self.user = User.objects.create_user(username='requester', password='password')
        self.approver = User.objects.create_user(username='approver', password='password')
        self.approver.groups.add(self.approver_group)
        branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        for u in (self.user, self.approver):
            UserProfile.objects.create(user=u).branch_company.add(branch)

    def login(self, user):
        # RequireCompanyCodeMiddleware logout ทุกคนที่ session ไม่มี company_code
        self.client.force_login(user)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    def propose(self, **overrides):
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
        self.login(self.user)
        return self.client.post(reverse('proposeDistributorCandidate'), data)

    def approve(self, candidate, user=None, **data):
        self.login(user or self.approver)
        return self.client.post(reverse('approveDistributorCandidate', args=[candidate.pk]), data)

    def test_status_new_pending_in_system(self):
        vendors = [dict(OSM_SHOP)]
        _annotate_system_status(vendors, "osm")
        self.assertEqual(vendors[0]["place_id"], "node/555")
        self.assertEqual(vendors[0]["system_status"], "new")

        self.propose()
        vendors = [dict(OSM_SHOP)]
        _annotate_system_status(vendors, "osm")
        self.assertEqual(vendors[0]["system_status"], "pending")

        Distributor.objects.create(id="V001", name="x", place_source="osm", place_id="node/555")
        vendors = [dict(OSM_SHOP)]
        _annotate_system_status(vendors, "osm")
        self.assertEqual(vendors[0]["system_status"], "in_system")
        self.assertEqual(vendors[0]["distributor_id"], "V001")

    def test_osm_way_and_node_with_same_number_are_different_places(self):
        Distributor.objects.create(id="V001", name="x", place_source="osm", place_id="way/555")
        vendors = [dict(OSM_SHOP)]
        _annotate_system_status(vendors, "osm")
        self.assertEqual(vendors[0]["system_status"], "new")

    def test_propose_creates_pending_candidate(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.assertEqual(c.status, DistributorCandidate.STATUS_PENDING)
        self.assertEqual(c.requested_by, self.user)
        self.assertEqual(c.latitude, Decimal("13.756331"))
        # เสนอซ้ำไม่สร้างรายการใหม่
        self.propose()
        self.assertEqual(DistributorCandidate.objects.count(), 1)

    def test_approve_new_creates_distributor_with_place_fields(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.approve(c, mode="new", distributor_id="V900", name="บจก. เจริญการช่าง", address="", tel="")

        d = Distributor.objects.get(id="V900")
        self.assertEqual(d.name, "บจก. เจริญการช่าง")
        self.assertEqual(d.address, OSM_SHOP["address"])  # ช่องว่าง -> ใช้ค่าจากแผนที่
        self.assertEqual((d.place_source, d.place_id), ("osm", "node/555"))
        self.assertEqual((d.latitude, d.longitude), (Decimal("13.756331"), Decimal("100.501765")))
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_APPROVED)
        self.assertEqual(c.distributor, d)
        self.assertEqual(c.reviewed_by, self.approver)

    def test_approve_new_rejects_existing_express_id(self):
        Distributor.objects.create(id="V900", name="ร้านอื่น")
        self.propose()
        c = DistributorCandidate.objects.get()
        self.approve(c, mode="new", distributor_id="V900")
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_PENDING)
        self.assertIsNone(Distributor.objects.get(id="V900").place_id)

    def test_approve_link_accepts_autocomplete_value_with_dash_in_id(self):
        Distributor.objects.create(id="D-01", name="เจริญการช่าง")
        self.propose()
        c = DistributorCandidate.objects.get()
        self.approve(c, mode="link", distributor_id="D-01-เจริญการช่าง")
        d = Distributor.objects.get(id="D-01")
        self.assertEqual(d.place_id, "node/555")
        self.assertEqual(d.name, "เจริญการช่าง")  # ผูกรายเดิม ไม่ทับชื่อ
        self.assertEqual(Distributor.objects.count(), 1)

    def test_user_outside_group_cannot_approve(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.approve(c, user=self.user, mode="new", distributor_id="V900")
        self.assertFalse(Distributor.objects.filter(id="V900").exists())
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_PENDING)

    def test_rejected_can_be_proposed_again(self):
        self.propose()
        c = DistributorCandidate.objects.get()
        self.login(self.approver)
        self.client.post(reverse('rejectDistributorCandidate', args=[c.pk]))
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_REJECTED)

        self.propose()
        c.refresh_from_db()
        self.assertEqual(c.status, DistributorCandidate.STATUS_PENDING)
        self.assertIsNone(c.reviewed_by)

    def test_propose_redirect_ignores_external_next(self):
        response = self.propose(next="https://evil.example.com/")
        self.assertEqual(response.url, reverse('viewVendorReport'))

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

    def test_candidate_page_shows_approve_forms_only_to_group(self):
        self.propose()
        self.login(self.approver)
        response = self.client.get(reverse('distributorCandidateList'))
        self.assertContains(response, OSM_SHOP["name"])
        self.assertContains(response, "อนุมัติ + สร้างใหม่")

        self.login(self.user)
        response = self.client.get(reverse('distributorCandidateList'))
        self.assertContains(response, OSM_SHOP["name"])
        self.assertNotContains(response, "อนุมัติ + สร้างใหม่")
