from django.test import TestCase

from stock.forms import (
    address_company_queryset,
    PurchaseOrderAddressCompanyForm,
    PurchaseRequisitionAddressCompanyForm,
    ComparisonPriceAddressCompanyForm,
    MaintenanceAddressCompanyForm,
)
from stock.models import (
    BaseAddress,
    BaseBranchCompany,
    BranchCompanyBaseAdress,
    PurchaseOrder,
    PurchaseRequisition,
    ComparisonPrice,
    Maintenance,
)


class AddressCompanyFilteringTestCase(TestCase):
    """address_company choices must be scoped to a single branch_company.code."""

    @classmethod
    def setUpTestData(cls):
        cls.branch_abc = BaseBranchCompany.objects.create(id="ABC", code="ABC", name="ABC Co")
        cls.branch_xyz = BaseBranchCompany.objects.create(id="XYZ", code="XYZ", name="XYZ Co")

        cls.addr_abc = [
            BaseAddress.objects.create(name_th=f"ABC addr {i}", address=f"{i} ABC Rd")
            for i in range(1, 4)
        ]
        cls.addr_xyz = [
            BaseAddress.objects.create(name_th=f"XYZ addr {i}", address=f"{i} XYZ Rd")
            for i in range(1, 3)
        ]
        for a in cls.addr_abc:
            BranchCompanyBaseAdress.objects.create(branch_company=cls.branch_abc, address=a)
        for a in cls.addr_xyz:
            BranchCompanyBaseAdress.objects.create(branch_company=cls.branch_xyz, address=a)

    # --- helper -----------------------------------------------------------
    def test_helper_returns_only_matching_branch_addresses(self):
        qs = address_company_queryset("ABC")
        self.assertCountEqual(list(qs), self.addr_abc)
        for a in self.addr_xyz:
            self.assertNotIn(a, qs)

    def test_helper_accepts_branch_instance(self):
        qs = address_company_queryset(self.branch_xyz)
        self.assertCountEqual(list(qs), self.addr_xyz)

    def test_helper_empty_when_code_missing(self):
        self.assertEqual(list(address_company_queryset(None)), [])
        self.assertEqual(list(address_company_queryset("")), [])

    def test_helper_empty_for_unknown_code(self):
        self.assertEqual(list(address_company_queryset("NOPE")), [])

    # --- forms ----------------------------------------------------------
    def _assert_form_scoped(self, form_cls, instance):
        form = form_cls(instance=instance)
        qs = form.fields["address_company"].queryset
        self.assertCountEqual(list(qs), self.addr_abc)
        for a in self.addr_xyz:
            self.assertNotIn(a, qs)

    def test_po_form_scoped(self):
        self._assert_form_scoped(
            PurchaseOrderAddressCompanyForm, PurchaseOrder(branch_company=self.branch_abc)
        )

    def test_pr_form_scoped(self):
        self._assert_form_scoped(
            PurchaseRequisitionAddressCompanyForm,
            PurchaseRequisition(branch_company=self.branch_abc),
        )

    def test_cp_form_scoped(self):
        self._assert_form_scoped(
            ComparisonPriceAddressCompanyForm, ComparisonPrice(branch_company=self.branch_abc)
        )

    def test_ma_form_scoped(self):
        self._assert_form_scoped(
            MaintenanceAddressCompanyForm, Maintenance(branch_company=self.branch_abc)
        )

    def test_different_codes_return_different_choices(self):
        po_abc = PurchaseOrderAddressCompanyForm(instance=PurchaseOrder(branch_company=self.branch_abc))
        po_xyz = PurchaseOrderAddressCompanyForm(instance=PurchaseOrder(branch_company=self.branch_xyz))
        self.assertCountEqual(list(po_abc.fields["address_company"].queryset), self.addr_abc)
        self.assertCountEqual(list(po_xyz.fields["address_company"].queryset), self.addr_xyz)

    def test_no_branch_company_exposes_nothing(self):
        form = PurchaseOrderAddressCompanyForm(instance=PurchaseOrder())
        self.assertEqual(list(form.fields["address_company"].queryset), [])

    # --- validation / security ----------------------------------------
    def test_foreign_branch_address_id_rejected_on_post(self):
        foreign = self.addr_xyz[0]
        form = PurchaseOrderAddressCompanyForm(
            data={"address_company": foreign.pk},
            instance=PurchaseOrder(branch_company=self.branch_abc),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("address_company", form.errors)

    def test_own_branch_address_id_accepted_on_post(self):
        own = self.addr_abc[0]
        form = PurchaseOrderAddressCompanyForm(
            data={"address_company": own.pk},
            instance=PurchaseOrder(branch_company=self.branch_abc),
        )
        self.assertTrue(form.is_valid(), form.errors)
