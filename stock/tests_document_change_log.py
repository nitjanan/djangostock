import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from stock.models import (
    BaseAddress,
    BaseApproveStatus,
    BaseBranchCompany,
    BaseCredit,
    BasePermission,
    BaseUnit,
    BaseVatType,
    BranchCompanyBaseAdress,
    ComparisonPrice,
    ComparisonPriceDistributor,
    ComparisonPriceItem,
    Distributor,
    DocumentChangeLog,
    PurchaseOrder,
    PurchaseOrderItem,
    Requisition,
    RequisitionItem,
)


class DocumentChangeLogTestCase(TestCase):
    """log การแก้ไขใบเปรียบเทียบราคา / ใบสั่งซื้อ และ item ในใบ"""

    def setUp(self):
        self.user = User.objects.create_user(username='log_user', password='password')
        self.examiner = User.objects.create_user(username='log_exam', password='password')
        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.vat_type = BaseVatType.objects.create(id="1", name="Vat 7%")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)
        self.credit = BaseCredit.objects.create(name="Cash")
        self.distributor = Distributor.objects.create(
            id="dist_log", name="Test Distributor", credit=self.credit, vat_type=self.vat_type,
        )
        self.unit = BaseUnit.objects.create(name="ชิ้น")
        for i, name in ((1, "รอดำเนินการ"), (2, "อนุมัติ"), (3, "ไม่อนุมัติ"), (4, "ไม่ต้องอนุมัติ")):
            BaseApproveStatus.objects.create(id=i, name=name)
        requisit = Requisition.objects.create(
            purchase_requisition_id=1, pr_ref_no="PR-LOG-001", name=self.user,
            chief_approve_user_name=self.user, supplies_approve_user_name=self.user,
            branch_company=self.branch,
        )
        self.req_item = RequisitionItem.objects.create(
            requisition_id=1, requisit=requisit, product_name="Item", quantity=5, quantity_pr=5,
        )

    def _logs(self, **kwargs):
        return DocumentChangeLog.objects.filter(**kwargs).order_by('id')

    def _make_po(self):
        return PurchaseOrder.objects.create(
            vat_type=self.vat_type, ref_no="PO-LOG-001", distributor=self.distributor,
            stockman_user=self.user, branch_company=self.branch, address_company=self.address,
            approver_status_id=1, amount=Decimal('107.00'),
        )

    def _make_cp(self):
        return ComparisonPrice.objects.create(
            organizer=self.user, branch_company=self.branch, address_company=self.address,
            examiner_status_id=1, approver_status_id=1, ref_no="CM-LOG-001", is_draft=False,
        )

    # ---------- ใบสั่งซื้อ ----------
    def test_create_po_is_logged(self):
        po = self._make_po()
        log = self._logs(model_name='PurchaseOrder', object_id=po.id).get()
        self.assertEqual(log.action, 'create')
        self.assertEqual((log.doc_type, log.doc_id, log.doc_ref_no), ('PO', po.id, 'PO-LOG-001'))
        self.assertEqual(log.changes['amount'], '107.00')

    def test_update_po_logs_old_and_new_values(self):
        po = self._make_po()
        po.amount = Decimal('200.00')
        po.shipping = 'EMS'
        po.save()
        log = self._logs(model_name='PurchaseOrder', action='update').get()
        self.assertEqual(log.changes['amount'], {'old': '107.00', 'new': '200.00'})
        self.assertEqual(log.changes['shipping'], {'old': '', 'new': 'EMS'})
        self.assertEqual(set(log.changes), {'amount', 'shipping'})

    def test_save_without_change_is_not_logged(self):
        po = self._make_po()
        po.refresh_from_db()
        po.save()
        self.assertFalse(self._logs(model_name='PurchaseOrder', action='update').exists())

    def test_foreign_key_change_shows_id_and_name(self):
        po = self._make_po()
        po.credit = self.credit
        po.save()
        change = self._logs(action='update').get().changes['credit']
        self.assertIsNone(change['old'])
        self.assertEqual(change['new'], '{}: {}'.format(self.credit.id, self.credit))

    def test_po_item_update_and_delete_are_logged_under_po(self):
        po = self._make_po()
        item = PurchaseOrderItem.objects.create(
            po=po, item=self.req_item, quantity=Decimal('5'), unit=self.unit,
            unit_price=Decimal('20'), price=Decimal('100.00'),
        )
        item.quantity = Decimal('3')
        item.save()
        PurchaseOrderItem.objects.filter(po=po).delete()

        logs = list(self._logs(model_name='PurchaseOrderItem'))
        self.assertEqual([log.action for log in logs], ['create', 'update', 'delete'])
        for log in logs:
            self.assertEqual((log.doc_type, log.doc_id, log.doc_ref_no), ('PO', po.id, 'PO-LOG-001'))
        self.assertEqual(logs[1].changes['quantity'], {'old': '5.0000', 'new': '3'})

    # ---------- ใบเปรียบเทียบราคา ----------
    def test_cp_distributor_and_item_are_logged_under_cp(self):
        cp = self._make_cp()
        cpd = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            amount=Decimal('107.00'),
        )
        cpi = ComparisonPriceItem.objects.create(
            item=self.req_item, quantity=Decimal('5'), unit=self.unit, bidder=cpd, cp=cp.id,
            unit_price=Decimal('20'), price=Decimal('100.00'),
        )
        cpi.price = Decimal('90.00')
        cpi.save()

        for model_name in ('ComparisonPriceDistributor', 'ComparisonPriceItem'):
            for log in self._logs(model_name=model_name):
                self.assertEqual((log.doc_type, log.doc_id, log.doc_ref_no), ('CP', cp.id, 'CM-LOG-001'))
        update = self._logs(model_name='ComparisonPriceItem', action='update').get()
        self.assertEqual(update.changes, {'price': {'old': '100.00', 'new': '90.00'}})

    def test_delete_cp_logs_cascade_children(self):
        cp = self._make_cp()
        cpd = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
        )
        ComparisonPriceItem.objects.create(item=self.req_item, unit=self.unit, bidder=cpd, cp=cp.id)
        cp_id = cp.id
        cp.delete()
        deleted = set(self._logs(doc_type='CP', doc_id=cp_id, action='delete').values_list('model_name', flat=True))
        self.assertEqual(deleted, {'ComparisonPrice', 'ComparisonPriceDistributor', 'ComparisonPriceItem'})

    # ---------- ผู้แก้ไข (จาก request) ----------
    def test_edit_through_view_records_user_and_path(self):
        BasePermission.objects.create(
            codename='CASCP', name='special', ap_amount_min=Decimal('200000'), ap_amount_max=Decimal('99999999'),
        )
        cp = self._make_cp()
        ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            amount=Decimal('107.00'),
        )
        client = Client()
        client.force_login(self.user)
        session = client.session
        session['company_code'] = 'HO'
        session.save()

        url = reverse('printComparePricePO', args=(cp.id,))
        response = client.post(url, {
            'btnSaveDraft': '', 'select_bidder': self.distributor.id, 'address_company': self.address.id,
            'examiner_user': self.examiner.id, 'note': 'ทดสอบ',
        })
        self.assertEqual(response.status_code, 302)

        log = self._logs(model_name='ComparisonPrice', object_id=cp.id, action='update').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.path, url)
        self.assertEqual(log.changes['is_draft'], {'old': False, 'new': True})
        self.assertEqual(log.changes['note'], {'old': None, 'new': 'ทดสอบ'})

    def test_change_outside_request_has_no_user(self):
        po = self._make_po()
        self.assertIsNone(self._logs(object_id=po.id).get().user)

    def test_log_failure_does_not_break_document_save(self):
        from unittest import mock
        from django.db import DatabaseError, transaction

        with mock.patch.object(DocumentChangeLog.objects, 'create', side_effect=DatabaseError('boom')):
            with transaction.atomic():
                po = self._make_po()
                po.amount = Decimal('300.00')
                po.save()
        po.refresh_from_db()
        self.assertEqual(po.amount, Decimal('300.00'))

    # ---------- เก็บข้อมูลก่อนลบ ----------
    def test_delete_log_keeps_full_row_before_delete(self):
        po = self._make_po()
        item = PurchaseOrderItem.objects.create(
            po=po, item=self.req_item, quantity=Decimal('5'), unit=self.unit,
            unit_price=Decimal('20'), price=Decimal('100.00'),
        )
        item_id = item.id
        #ค่าในหน่วยความจำที่ยังไม่ได้ save ต้องไม่ถูกเก็บ ต้องเป็นค่าในฐานข้อมูลก่อนลบ
        item.quantity = Decimal('999')
        item.delete()

        log = self._logs(model_name='PurchaseOrderItem', action='delete').get()
        self.assertEqual(log.object_id, item_id)
        self.assertEqual((log.doc_type, log.doc_id, log.doc_ref_no), ('PO', po.id, 'PO-LOG-001'))
        data = log.changes
        self.assertEqual(data['quantity'], '5.0000')
        self.assertEqual(data['price'], '100.00')
        self.assertEqual(data['unit'], '{}: {}'.format(self.unit.id, self.unit))
        #เก็บทุกช่อง รวมช่องว่างและวันที่
        self.assertIn('discount', data)
        self.assertIsNone(data['discount'])
        self.assertEqual(data['description'], '')
        self.assertIn('created', data)
        self.assertIn('update', data)

    def test_delete_cp_keeps_parent_ref_for_children(self):
        cp = self._make_cp()
        cpd = ComparisonPriceDistributor.objects.create(
            cp=cp, distributor=self.distributor, credit=self.credit, vat_type=self.vat_type,
            amount=Decimal('107.00'),
        )
        ComparisonPriceItem.objects.create(item=self.req_item, unit=self.unit, bidder=cpd, cp=cp.id, price=Decimal('100.00'))
        cp.delete()
        for log in self._logs(action='delete'):
            self.assertEqual(log.doc_ref_no, 'CM-LOG-001')
        cp_log = self._logs(model_name='ComparisonPrice', action='delete').get()
        self.assertEqual(cp_log.changes['ref_no'], 'CM-LOG-001')
        self.assertEqual(cp_log.changes['organizer'], '{}: {}'.format(self.user.id, self.user))

    def test_rolled_back_delete_leaves_no_log(self):
        from django.db import transaction

        po = self._make_po()
        po_id = po.pk
        try:
            with transaction.atomic():
                po.delete()
                raise RuntimeError('rollback')
        except RuntimeError:
            pass
        self.assertTrue(PurchaseOrder.objects.filter(pk=po_id).exists())
        self.assertFalse(self._logs(action='delete').exists())
