from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from stock.filters import PurchaseOrderFilter
from stock.models import (
    BaseAddress, BaseApproveStatus, BaseBranchCompany, BaseUnit, BaseVatType,
    Category, Distributor, Product, PurchaseOrder, PurchaseOrderItem,
    Requisition, RequisitionItem,
)


class _POFilterBase(TestCase):
    """Shared fixture + `_po` helper for PurchaseOrderFilter tests. Holds no tests of its own."""

    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        cls.vat = BaseVatType.objects.create(id="1", name="VAT 7%")
        cls.unit = BaseUnit.objects.create(name="ชิ้น")
        cls.status = BaseApproveStatus.objects.create(name="อนุมัติ")
        cls.category = Category.objects.create(name="Cat", slug="cat")
        cls.user = User.objects.create_user(username="req_user", password="pw")
        cls.distributor = Distributor.objects.create(id="D-1", name="Shop")


    @classmethod
    def _po(cls, ref_no, product_codes, unit_prices=None, machines=None, category=None,
            pr_ref_nos=None, amount="1"):
        po = PurchaseOrder.objects.create(
            vat_type=cls.vat, distributor=cls.distributor, approver_status=cls.status,
            address_company=cls.address, ref_no=ref_no, total_price=Decimal(amount),
            total_after_discount=Decimal(amount), vat=Decimal("0"), amount=Decimal(amount),
        )
        for i, code in enumerate(product_codes):
            rq = Requisition.objects.create(
                name=cls.user, chief_approve_user_name=cls.user,
                supplies_approve_user_name=cls.user, branch_company=cls.branch,
                address_company=cls.address, ref_no="RQ-%s-%d" % (ref_no, i),
                pr_ref_no=pr_ref_nos[i] if pr_ref_nos else None,
            )
            product = Product.objects.get_or_create(
                id=code, defaults={"name": code, "slug": "slug-" + code,
                                   "category": category or cls.category})[0]
            item = RequisitionItem.objects.create(
                requisition_id=rq.id, requisit=rq, product=product, product_name=code,
                machine=machines[i] if machines else "", quantity=Decimal("1"),
            )
            price = Decimal(unit_prices[i]) if unit_prices else Decimal("1")
            PurchaseOrderItem.objects.create(
                po=po, item=item, unit=cls.unit, quantity=Decimal("1"),
                unit_price=price, price=price,
            )
        return po

    def _filter(self, params):
        return list(PurchaseOrderFilter(params, queryset=PurchaseOrder.objects.all()).qs.distinct())

    def _refs(self, params):
        return sorted(po.ref_no for po in self._filter(params))


class PurchaseOrderFilterProductRangeTestCase(_POFilterBase):
    """item_product_id_from / item_product_id_to must match one PO item inside
    the range, not "some item >= from" and "another item <= to"."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # PO มีสินค้าในช่วง
        cls.po_in = cls._po("PO-IN", ["RB-GT-020"])
        # PO มีสินค้าก่อนช่วง และหลังช่วง แต่ไม่มีสินค้าในช่วง
        cls.po_out = cls._po("PO-OUT", ["AA-000", "ZZ-999"])

    def test_range_excludes_po_without_item_in_range(self):
        result = self._filter({"item_product_id_from": "RB-GT-019", "item_product_id_to": "RB-GT-035"})
        self.assertEqual(result, [self.po_in])

    def test_range_is_case_insensitive_like_user_input(self):
        result = self._filter({"item_product_id_from": "rb-gt-019", "item_product_id_to": "rb-gt-035"})
        self.assertEqual(result, [self.po_in])

    def test_only_from(self):
        result = self._filter({"item_product_id_from": "RB-GT-019"})
        self.assertCountEqual(result, [self.po_in, self.po_out])

    def test_only_to(self):
        result = self._filter({"item_product_id_to": "RB-GT-035"})
        self.assertCountEqual(result, [self.po_in, self.po_out])


class PurchaseOrderFilterSameItemTestCase(_POFilterBase):
    """Item-level filters used together must all hold on the same PO item."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_category = Category.objects.create(name="Other", slug="other")
        # รายการที่ 1: ราคา 50 ระบบงาน MC-A / รายการที่ 2: ราคา 500 ระบบงาน MC-B
        cls.po_mixed = cls._po("PO-MIXED", ["P-CHEAP", "P-EXPENSIVE"],
                               unit_prices=["50", "500"], machines=["MC-A", "MC-B"])
        cls.po_other_cat = cls._po("PO-OTHERCAT", ["Q-001"], category=cls.other_category)

    def test_unit_price_range_must_match_one_item(self):
        # ไม่มีรายการไหนราคาอยู่ระหว่าง 100-200 แม้จะมีรายการ >=100 และ <=200 แยกกัน
        self.assertEqual(self._refs({"unit_price_min": "100", "unit_price_max": "200"}), [])
        self.assertEqual(self._refs({"unit_price_min": "400", "unit_price_max": "600"}), ["PO-MIXED"])

    def test_machine_and_price_must_match_one_item(self):
        self.assertEqual(self._refs({"item_machine": "MC-A", "unit_price_min": "400"}), [])
        self.assertEqual(self._refs({"item_machine": "MC-B", "unit_price_min": "400"}), ["PO-MIXED"])

    def test_product_name_and_product_range_must_match_one_item(self):
        self.assertEqual(self._refs({"item_product_name": "P-CHEAP",
                                     "item_product_id_from": "P-E", "item_product_id_to": "P-F"}), [])

    def test_category(self):
        self.assertEqual(self._refs({"category": self.other_category.pk}), ["PO-OTHERCAT"])

    def test_invalid_number_is_ignored_not_matched_as_zero(self):
        f = PurchaseOrderFilter({"unit_price_min": "abc"}, queryset=PurchaseOrder.objects.all())
        self.assertIn("unit_price_min", f.form.errors)
        self.assertEqual(f.qs.distinct().count(), 2)

    def test_amount_range(self):
        self._po("PO-BIG", ["R-001"], amount="5000")
        self.assertEqual(self._refs({"amount_min": "1000", "amount_max": "9999"}), ["PO-BIG"])


class PurchaseOrderFilterPrRefNoTestCase(_POFilterBase):
    """pr_ref_no must also find POs whose items come from a PR other than po.pr,
    the same PR numbers the report table shows."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.po_multi_pr = cls._po("PO-MULTIPR", ["S-001", "S-002"],
                                  pr_ref_nos=["RS-0007", "RS-0008"])

    def test_finds_po_by_pr_of_any_item(self):
        self.assertEqual(self._refs({"pr_ref_no": "RS-0008"}), ["PO-MULTIPR"])
