from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from stock.models import BaseBranchCompany, BaseCredit, BaseVatType, Distributor, UserProfile


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
