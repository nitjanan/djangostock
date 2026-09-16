import datetime
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BasePOType,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    Distributor,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    Requisition,
    RequisitionItem,
    UserProfile,
)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ShowPOApproverUserTestCase(TestCase):
    """showPO: แสดงชื่อผู้อนุมัติ แม้ยังไม่อนุมัติ (ลายเซ็นแสดงเฉพาะเมื่ออนุมัติแล้ว)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='tester_show_po', password='password', first_name='สมชาย', last_name='ใจดี'
        )
        approver_group, _ = Group.objects.get_or_create(name='ผู้อนุมัติ')
        self.user.groups.add(approver_group)
        self.client.login(username='tester_show_po', password='password')

        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_show", name="Test Distributor", credit=self.credit, vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(id="po_type_show", name="Standard PO")
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        BaseApproveStatus.objects.create(id=1, name="รอดำเนินการ")
        BaseApproveStatus.objects.create(id=2, name="อนุมัติ")
        UserProfile.objects.create(user=self.user).branch_company.add(self.branch)

        self.requisit = Requisition.objects.create(
            purchase_requisition_id=1,
            pr_ref_no="PR-SHOW-001",
            name=self.user,
            chief_approve_user_name=self.user,
            supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        PurchaseRequisition.objects.create(requisition=self.requisit, branch_company=self.branch)
        self.req_item = RequisitionItem.objects.create(
            requisition_id=1, requisit=self.requisit, product_name="Test Item", quantity=1, quantity_pr=1
        )

    def _po(self, approver_status_id):
        po = PurchaseOrder.objects.create(
            vat_type=self.vat_type,
            ref_no="PO-SHOW-%s" % approver_status_id,
            distributor=self.distributor,
            credit=self.credit,
            stockman_user=self.user,
            approver_user=self.user,
            approver_status_id=approver_status_id,
            branch_company=self.branch,
            address_company=self.address,
            po_type=self.po_type,
            total_price=Decimal('100.00'),
            amount=Decimal('107.00'),
            due_receive_update=datetime.date(2026, 7, 20),
        )
        PurchaseOrderItem.objects.create(
            po=po, item=self.req_item, quantity=Decimal('1.0000'), unit=self.unit,
            unit_price=Decimal('100.0000'), price=Decimal('100.00'),
        )
        return po

    def test_shows_approver_name_when_pending(self):
        po = self._po(1)
        html = self.client.get(reverse('showPO', kwargs={'po_id': po.id, 'mode': 1})).content.decode('utf-8')
        self.assertIn(str(self.user), html)

    def test_shows_approver_name_when_approved(self):
        po = self._po(2)
        html = self.client.get(reverse('showPO', kwargs={'po_id': po.id, 'mode': 1})).content.decode('utf-8')
        self.assertIn(str(self.user), html)

    def test_signature_only_when_approved(self):
        signature = 'userprofile.signature'
        po_pending = self._po(1)
        html_pending = self.client.get(
            reverse('showPO', kwargs={'po_id': po_pending.id, 'mode': 1})
        ).content.decode('utf-8')
        po_approved = self._po(2)
        html_approved = self.client.get(
            reverse('showPO', kwargs={'po_id': po_approved.id, 'mode': 1})
        ).content.decode('utf-8')
        self.assertLess(html_pending.count('width="160" height="75"'), html_approved.count('width="160" height="75"'))
