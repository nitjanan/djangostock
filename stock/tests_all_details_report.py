from decimal import Decimal
import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from stock.models import (
    UserProfile, BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress,
    BaseVatType, BaseUnit, BaseApproveStatus, Category,
    Product, Distributor, Requisition, RequisitionItem, PurchaseRequisition,
    ComparisonPrice, ComparisonPriceItem, ComparisonPriceDistributor,
    PurchaseOrder, PurchaseOrderItem,
)

URL_NAME = "viewAllDetailsReport"


class AllDetailsReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.other_branch = BaseBranchCompany.objects.create(id="2", code="BR", name="Branch")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        # Satisfy the address_company auto-lookup in model .save() for both branches.
        BranchCompanyBaseAdress.objects.create(branch_company=cls.branch, address=cls.address)
        BranchCompanyBaseAdress.objects.create(branch_company=cls.other_branch, address=cls.address)
        cls.vat = BaseVatType.objects.create(id="1", name="VAT 7%")
        cls.unit = BaseUnit.objects.create(name="ชิ้น")
        cls.status_approved = BaseApproveStatus.objects.create(name="อนุมัติ")
        cls.category = Category.objects.create(name="Cat", slug="cat")

        cls.user = User.objects.create_user(username="reporter", password="pw")
        profile = UserProfile.objects.create(user=cls.user)
        profile.branch_company.add(cls.branch, cls.other_branch)

        cls.requester = User.objects.create_user(username="req_user", password="pw",
                                                 first_name="Somchai", last_name="Jaidee")
        cls.approver = User.objects.create_user(username="appr_user", password="pw")

    def setUp(self):
        self.client = Client()
        self.client.login(username="reporter", password="pw")
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    # ----- fixture helper reused by later tasks -----
    @classmethod
    def _build_chain(cls, *, code="HO", stage="PO", product_code="P001",
                     product_name="Computer", distributor_name="ABC Company",
                     rq_ref="REQ-2026-001", pr_ref="PR-00125", cp_ref="CP-0007",
                     po_ref="PO-0056", qty="2.0000", price="1000.00", n_po_items=1):
        """Build a procurement chain up to `stage` in {'RQ','PR','CP','PO'}.
        Returns a dict of the created objects."""
        branch = BaseBranchCompany.objects.get(code=code)
        product = Product.objects.create(id=product_code, name=product_name + " " + product_code,
                                         slug="slug-" + product_code, category=cls.category)
        distributor = Distributor.objects.create(id="D-" + product_code, name=distributor_name)

        rq = Requisition.objects.create(
            name=cls.requester, chief_approve_user_name=cls.approver,
            supplies_approve_user_name=cls.approver, branch_company=branch,
            address_company=cls.address, ref_no=rq_ref, pr_ref_no=pr_ref,
        )
        item = RequisitionItem.objects.create(
            requisition_id=rq.id, requisit=rq, product=product,
            product_name=product_name, machine="MC-1", description="desc",
            quantity=Decimal(qty),
        )
        out = {"branch": branch, "product": product, "distributor": distributor,
               "rq": rq, "item": item, "pr": None, "cp": None, "cpd": None,
               "cpi": None, "po": None, "po_items": []}
        if stage == "RQ":
            return out

        pr = PurchaseRequisition.objects.create(
            requisition=rq, branch_company=branch, address_company=cls.address, ref_no=pr_ref,
        )
        out["pr"] = pr
        if stage == "PR":
            return out

        cp = ComparisonPrice.objects.create(
            organizer=cls.approver, branch_company=branch, address_company=cls.address,
            ref_no=cp_ref, select_bidder=distributor,
        )
        cpd = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=distributor, vat_type=cls.vat, is_select=True,
            amount=Decimal(price),
        )
        cpi = ComparisonPriceItem.objects.create(
            item=item, bidder=cpd, unit=cls.unit, quantity=Decimal(qty),
            unit_price=Decimal(price), price=Decimal(price),
        )
        out.update(cp=cp, cpd=cpd, cpi=cpi)
        if stage == "CP":
            return out

        po = PurchaseOrder.objects.create(
            vat_type=cls.vat, cp=cp, pr=pr, distributor=distributor,
            approver_status=cls.status_approved, address_company=cls.address,
            ref_no=po_ref, amount=Decimal(price),
        )
        out["po"] = po
        for i in range(n_po_items):
            out["po_items"].append(PurchaseOrderItem.objects.create(
                po=po, item=item, unit=cls.unit, quantity=Decimal(qty),
                unit_price=Decimal(price), price=Decimal(price),
            ))
        return out

    # ----- Task 1 test -----
    def test_page_loads_empty_db(self):
        resp = self.client.get(reverse(URL_NAME))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "report/viewAllDetails.html")
        self.assertEqual(list(resp.context["rows"]), [])
        self.assertEqual(resp.context["dashboard"]["requisition_items"], 0)
