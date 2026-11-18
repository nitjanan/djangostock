import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from stock.models import (
    BaseAddress, BaseBranchCompany, BaseCredit, BaseVatType, BranchCompanyBaseAdress, ComparisonPrice, ComparisonPriceDistributor,
    Distributor, PurchaseOrder, UserProfile,
)


class SearchDataDistributorTestCase(TestCase):
    """ajax searchDataDistributor: ผู้จำหน่ายที่ไม่ได้ตั้งเครดิต / ชนิดภาษี ต้องไม่ error (หัวเอกสาร PO ไม่ขึ้นชื่อ)"""

    def setUp(self):
        branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        user = User.objects.create_user(username="user", password="pw")
        UserProfile.objects.create(user=user).branch_company.add(branch)
        self.client.force_login(user)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    def get(self, distributor_id):
        return self.client.get(reverse("searchDataDistributor"), {"id_distributor": distributor_id})

    def test_distributor_without_credit_and_vat_type(self):
        Distributor.objects.create(id="01a175", name="เอสอาร์เอ็มบริการ", address="สุราษฎร์ธานี", tel="077-000000")

        response = self.get("01a175")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["credit"])
        self.assertIsNone(data["vat_type"])
        self.assertEqual(data["id"], "01a175")
        self.assertEqual(data["name"], "เอสอาร์เอ็มบริการ")
        self.assertEqual(data["address"], "สุราษฎร์ธานี")
        self.assertEqual(data["tel"], "077-000000")

    def test_distributor_with_credit_and_vat_type(self):
        credit = BaseCredit.objects.first() or BaseCredit.objects.create(name="15 วัน")
        vat_type = BaseVatType.objects.first() or BaseVatType.objects.create(name="แยก vat")
        Distributor.objects.create(id="D-1", name="Shop", credit=credit, vat_type=vat_type)

        data = self.get("D-1").json()

        self.assertEqual(data["credit"], credit.id)
        self.assertEqual(data["vat_type"], vat_type.id)


class SearchDataDistributorFallbackTestCase(TestCase):
    """ผู้จำหน่ายที่ไม่ได้ตั้งเครดิต / ชนิดภาษี: ดึงค่าล่าสุดที่เคยบันทึกในใบเปรียบเทียบราคา / ใบสั่งซื้อแทน"""

    def setUp(self):
        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.user = User.objects.create_user(username="user", password="pw")
        UserProfile.objects.create(user=self.user).branch_company.add(self.branch)
        self.client.force_login(self.user)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()
        self.address = BaseAddress.objects.create(name_th="FB Company", address="1 FB St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.c15 = BaseCredit.objects.create(name="FB 15 วัน")
        self.c30 = BaseCredit.objects.create(name="FB 30 วัน")
        self.c60 = BaseCredit.objects.create(name="FB 60 วัน")
        self.vat_in = BaseVatType.objects.get_or_create(id=1, defaults={"name": "รวม vat"})[0]
        self.vat_out = BaseVatType.objects.get_or_create(id=2, defaults={"name": "แยก vat"})[0]
        self.dist = Distributor.objects.create(id="FB-1", name="No Terms Shop")

    def get(self):
        return self.client.get(reverse("searchDataDistributor"), {"id_distributor": self.dist.id}).json()

    def po(self, created, **kw):
        po = PurchaseOrder.objects.create(distributor=self.dist, branch_company=self.branch, address_company=self.address,
                                          stockman_user=self.user, **kw)
        PurchaseOrder.objects.filter(id=po.id).update(created=created)
        return po

    def cpd(self, created, is_cancel=False, **kw):
        cp = ComparisonPrice.objects.create(organizer=self.user, branch_company=self.branch, address_company=self.address,
                                            is_cancel=is_cancel)
        cpd = ComparisonPriceDistributor.objects.create(cp=cp, distributor=self.dist, **kw)
        ComparisonPriceDistributor.objects.filter(id=cpd.id).update(created=created)
        return cpd

    def test_no_history_returns_null(self):
        data = self.get()
        self.assertIsNone(data["credit"])
        self.assertIsNone(data["vat_type"])

    def test_uses_latest_between_po_and_cp(self):
        self.po(datetime.date(2026, 1, 10), credit=self.c15, vat_type=self.vat_in)
        self.cpd(datetime.date(2026, 3, 5), credit=self.c30, vat_type=self.vat_out)
        self.po(datetime.date(2026, 2, 1), credit=self.c60, vat_type=self.vat_in)

        data = self.get()

        self.assertEqual(data["credit"], self.c30.id)
        self.assertEqual(str(data["vat_type"]), str(self.vat_out.id))

    def test_skips_cancelled_and_empty_values(self):
        self.po(datetime.date(2026, 1, 10), credit=self.c15, vat_type=self.vat_in)
        self.po(datetime.date(2026, 4, 1), credit=self.c60, vat_type=self.vat_out, is_cancel=True)
        self.cpd(datetime.date(2026, 4, 2), credit=self.c30, vat_type=self.vat_in, is_cancel=True)
        #ใบล่าสุดไม่ได้ใส่เครดิต: ข้ามไปใบที่มีค่า
        self.cpd(datetime.date(2026, 4, 3), vat_type=self.vat_out)

        data = self.get()

        self.assertEqual(data["credit"], self.c15.id)
        self.assertEqual(str(data["vat_type"]), str(self.vat_out.id))

    def test_same_day_prefers_po(self):
        self.cpd(datetime.date(2026, 5, 1), credit=self.c30, vat_type=self.vat_out)
        self.po(datetime.date(2026, 5, 1), credit=self.c60, vat_type=self.vat_in)

        self.assertEqual(self.get()["credit"], self.c60.id)

    def test_distributor_value_wins_over_history(self):
        Distributor.objects.filter(id=self.dist.id).update(credit=self.c15, vat_type=self.vat_in)
        self.po(datetime.date(2026, 5, 1), credit=self.c60, vat_type=self.vat_out)

        data = self.get()

        self.assertEqual(data["credit"], self.c15.id)
        self.assertEqual(str(data["vat_type"]), str(self.vat_in.id))
