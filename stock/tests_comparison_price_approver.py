from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from stock.models import (
    BaseBranchCompany, BaseVatType, BaseAddress, BaseCredit, Distributor,
    ComparisonPrice, ComparisonPriceDistributor,
)


class ComparisonPriceApproverCompanyAwareTestCase(TestCase):
    """
    ตรวจสอบว่า findExaminerUserComparisonPrice / findApproveUserComparisonPrice
    เลือกสิทธิ (CAECP*/CAACP*) โดยยึดบริษัทของใบเปรียบเทียบเป็นเกณฑ์ด้วย
    ไม่ใช่แค่ช่วงยอดเงิน จึงรองรับ CAECP5/CAACP5/CAECP6/CAACP6 ของบริษัท 09
    ที่ช่วงยอดเงินซ้อนทับกับ CAECP2/CAACP2/CAECP3/CAACP3 ของบริษัทอื่น
    """

    def setUp(self):
        from django.test import RequestFactory
        from stock.models import (
            Position, BasePermission, PositionBasePermission, UserProfile,
        )
        from stock.views import (
            findExaminerUserComparisonPrice, findApproveUserComparisonPrice,
        )

        self.factory = RequestFactory()
        self.findExaminer = findExaminerUserComparisonPrice
        self.findApprover = findApproveUserComparisonPrice

        # --- บริษัท ---
        self.branch09 = BaseBranchCompany.objects.create(id="b09", code="09", name="Company 09")
        self.branch01 = BaseBranchCompany.objects.create(id="b01", code="01", name="Company 01")

        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Addr", address="x")
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="d1", name="Dist", credit=self.credit, vat_type=self.vat_type,
        )

        # --- BasePermission: ช่วงยอดเงินซ้อนทับกันข้ามบริษัทโดยตั้งใจ ---
        def bp(code, mn, mx):
            return BasePermission.objects.create(
                name=code, codename=code, codename_th=code + "-th",
                ap_amount_min=Decimal(mn), ap_amount_max=Decimal(mx),
            )

        # ระดับ CP2/CP5 : 1000 - 5000  (ทับกัน)
        self.caecp2 = bp("CAECP2", "1000.00", "5000.00")
        self.caecp5 = bp("CAECP5", "1000.00", "5000.00")
        self.caacp2 = bp("CAACP2", "1000.00", "5000.00")
        self.caacp5 = bp("CAACP5", "1000.00", "5000.00")
        # ระดับ CP3/CP6 : 5000.01 - 10000 (ทับกัน)
        self.caecp3 = bp("CAECP3", "5000.01", "10000.00")
        self.caecp6 = bp("CAECP6", "5000.01", "10000.00")
        self.caacp3 = bp("CAACP3", "5000.01", "10000.00")
        self.caacp6 = bp("CAACP6", "5000.01", "10000.00")

        # --- Position + PositionBasePermission (ผูกสิทธิกับบริษัท) ---
        def grant(name, permission, branch):
            pos = Position.objects.create(name=name)
            pbp = PositionBasePermission.objects.create(position=pos)
            pbp.base_permission.add(permission)
            pbp.branch_company.add(branch)
            return pos

        self.pos_e5_09 = grant("E CAECP5 @09", self.caecp5, self.branch09)
        self.pos_a5_09 = grant("A CAACP5 @09", self.caacp5, self.branch09)
        self.pos_e6_09 = grant("E CAECP6 @09", self.caecp6, self.branch09)
        self.pos_a6_09 = grant("A CAACP6 @09", self.caacp6, self.branch09)
        self.pos_e2_01 = grant("E CAECP2 @01", self.caecp2, self.branch01)
        self.pos_a2_01 = grant("A CAACP2 @01", self.caacp2, self.branch01)

        # --- ผู้ใช้ที่ถือแต่ละตำแหน่ง ---
        def make_user(username, position, branch):
            u = User.objects.create_user(username=username, password="x")
            p = UserProfile.objects.create(user=u, position=position)
            p.branch_company.add(branch)
            return u

        self.u_e5_09 = make_user("u_e5_09", self.pos_e5_09, self.branch09)
        self.u_a5_09 = make_user("u_a5_09", self.pos_a5_09, self.branch09)
        self.u_e6_09 = make_user("u_e6_09", self.pos_e6_09, self.branch09)
        self.u_a6_09 = make_user("u_a6_09", self.pos_a6_09, self.branch09)
        self.u_e2_01 = make_user("u_e2_01", self.pos_e2_01, self.branch01)
        self.u_a2_01 = make_user("u_a2_01", self.pos_a2_01, self.branch01)

        # ผู้ใช้ที่ยิง request (มองเห็นทั้งสองบริษัท)
        self.requester = User.objects.create_user(username="requester", password="x")
        rp = UserProfile.objects.create(user=self.requester)
        rp.branch_company.add(self.branch09, self.branch01)

    # ---------- helpers ----------
    def _request(self, company_code):
        req = self.factory.get("/")
        req.user = self.requester
        req.session = {"company_code": company_code}
        return req

    def _make_cp(self, branch, amount):
        cp = ComparisonPrice.objects.create(
            organizer=self.requester, select_bidder=self.distributor,
            address_company=self.address, branch_company=branch,
        )
        cpd = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.distributor, credit=self.credit,
            vat_type=self.vat_type, total_price=amount, amount=Decimal(amount),
        )
        return cp, cpd

    def _ids(self, qs):
        return {row["user__id"] for row in qs}

    # ---------- Test 1 - CAECP5 ----------
    def test_company09_amount_in_cp2_range_selects_caecp5(self):
        _, cpd = self._make_cp(self.branch09, "3000.00")
        examiner = self.findExaminer(self._request("09"), cpd.id, None)
        self.assertEqual(self._ids(examiner), {self.u_e5_09.id})

    # ---------- Test 2 - CAACP5 ----------
    def test_company09_amount_in_cp2_range_selects_caacp5(self):
        _, cpd = self._make_cp(self.branch09, "3000.00")
        approver = self.findApprover(self._request("09"), cpd.id, None)
        self.assertEqual(self._ids(approver), {self.u_a5_09.id})

    # ---------- Test 3 - CAECP6 ----------
    def test_company09_amount_in_cp3_range_selects_caecp6(self):
        _, cpd = self._make_cp(self.branch09, "7000.00")
        examiner = self.findExaminer(self._request("09"), cpd.id, None)
        self.assertEqual(self._ids(examiner), {self.u_e6_09.id})

    # ---------- Test 4 - CAACP6 ----------
    def test_company09_amount_in_cp3_range_selects_caacp6(self):
        _, cpd = self._make_cp(self.branch09, "7000.00")
        approver = self.findApprover(self._request("09"), cpd.id, None)
        self.assertEqual(self._ids(approver), {self.u_a6_09.id})

    # ---------- Test 5 - regression: other company still uses CAECP2/CAACP2 ----------
    def test_other_company_still_selects_caecp2_and_caacp2(self):
        _, cpd = self._make_cp(self.branch01, "3000.00")
        examiner = self.findExaminer(self._request("01"), cpd.id, None)
        approver = self.findApprover(self._request("01"), cpd.id, None)
        self.assertEqual(self._ids(examiner), {self.u_e2_01.id})
        self.assertEqual(self._ids(approver), {self.u_a2_01.id})

    # ---------- Test 6 - same amount, different companies ----------
    def test_same_amount_different_companies_pick_own_company_permission(self):
        _, cpd09 = self._make_cp(self.branch09, "3000.00")
        _, cpd01 = self._make_cp(self.branch01, "3000.00")

        self.assertEqual(
            self._ids(self.findExaminer(self._request("09"), cpd09.id, None)),
            {self.u_e5_09.id},
        )
        self.assertEqual(
            self._ids(self.findExaminer(self._request("01"), cpd01.id, None)),
            {self.u_e2_01.id},
        )
        # ต้องไม่มีสิทธิของอีกบริษัทหลุดเข้ามาเพราะช่วงยอดเงินซ้อนกัน
        self.assertNotIn(
            self.u_e2_01.id,
            self._ids(self.findExaminer(self._request("09"), cpd09.id, None)),
        )
        self.assertNotIn(
            self.u_e5_09.id,
            self._ids(self.findExaminer(self._request("01"), cpd01.id, None)),
        )

    # ---------- Boundary tests ----------
    def test_boundaries_inclusive_min_and_max(self):
        # amount == min -> included in CAECP5
        _, cpd_min = self._make_cp(self.branch09, "1000.00")
        self.assertEqual(
            self._ids(self.findExaminer(self._request("09"), cpd_min.id, None)),
            {self.u_e5_09.id},
        )
        # amount == max -> still CAECP5 (inclusive), not CAECP6
        _, cpd_max = self._make_cp(self.branch09, "5000.00")
        self.assertEqual(
            self._ids(self.findExaminer(self._request("09"), cpd_max.id, None)),
            {self.u_e5_09.id},
        )
        # amount just above max -> falls into CAECP6 range
        _, cpd_above = self._make_cp(self.branch09, "5000.01")
        self.assertEqual(
            self._ids(self.findExaminer(self._request("09"), cpd_above.id, None)),
            {self.u_e6_09.id},
        )
        # amount just below min -> no permission matches
        _, cpd_below = self._make_cp(self.branch09, "999.99")
        self.assertEqual(
            self._ids(self.findExaminer(self._request("09"), cpd_below.id, None)),
            set(),
        )
