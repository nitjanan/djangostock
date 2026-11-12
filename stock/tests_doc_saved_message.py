from django.contrib import messages
from django.contrib.messages.storage.cookie import CookieStorage
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase

from stock.models import ComparisonPrice, PurchaseOrder, PurchaseRequisition, Requisition
from stock.views import doc_saved_message, redirect_list_focus


class DocSavedMessageTestCase(SimpleTestCase):
    """ข้อความแจ้งผลหลังบันทึก ใบขอเบิก / ใบขอซื้อ / ใบเปรียบเทียบราคา / ใบสั่งซื้อ"""

    def _request(self):
        request = RequestFactory().post('/')
        request._messages = CookieStorage(request)
        return request

    def _message(self, doc):
        request = self._request()
        doc_saved_message(request, doc)
        return [str(m) for m in request._messages]

    def test_requisition_has_no_draft(self):
        self.assertEqual(self._message(Requisition(ref_no='RQ001')), ['บันทึกใบขอเบิก RQ001 เรียบร้อยแล้ว'])

    def test_pr_draft(self):
        pr = PurchaseRequisition(ref_no='RL16911002', is_draft=True, approver_status_id=1)
        self.assertEqual(self._message(pr), ['บันทึกแบบร่างใบขอซื้อ RL16911002 เรียบร้อยแล้ว'])

    def test_pr_send_for_approval(self):
        pr = PurchaseRequisition(ref_no='RL16911002', is_draft=False, approver_status_id=1)
        self.assertEqual(self._message(pr), ['บันทึกและส่งอนุมัติใบขอซื้อ RL16911002 เรียบร้อยแล้ว'])

    def test_cp_waiting_examiner(self):
        cp = ComparisonPrice(ref_no='CM001', is_draft=False, examiner_status_id=1, approver_status_id=1)
        self.assertEqual(self._message(cp), ['บันทึกและส่งอนุมัติใบเปรียบเทียบราคา CM001 เรียบร้อยแล้ว'])

    def test_po_already_approved_is_edit(self):
        po = PurchaseOrder(ref_no='S001', is_draft=False, approver_status_id=2)
        self.assertEqual(self._message(po), ['บันทึกการแก้ไขใบสั่งซื้อ S001 เรียบร้อยแล้ว'])

    def test_po_draft(self):
        po = PurchaseOrder(ref_no='S001', is_draft=True, approver_status_id=1)
        self.assertEqual(self._message(po), ['บันทึกแบบร่างใบสั่งซื้อ S001 เรียบร้อยแล้ว'])

    def test_redirect_list_focus_adds_message_only_with_request(self):
        po = PurchaseOrder(id=5, ref_no='S001', is_draft=False, approver_status_id=1)
        request = self._request()
        response = redirect_list_focus('viewPO', po, request)
        self.assertTrue(response.url.endswith('?tab=process&focus=5'))
        self.assertEqual([str(m) for m in request._messages], ['บันทึกและส่งอนุมัติใบสั่งซื้อ S001 เรียบร้อยแล้ว'])
        #ไม่ส่ง request (เช่น createPR / reApprovePR ที่มีข้อความของตัวเอง) ไม่เพิ่มข้อความ
        request2 = self._request()
        redirect_list_focus('viewPO', po)
        self.assertEqual(list(request2._messages), [])

    def test_alert_partial_renders_message(self):
        request = self._request()
        messages.info(request, 'ส่งอนุมัติใบขอซื้อ RL16911002 ใหม่เรียบร้อยแล้ว')
        html = render_to_string('_messages_alert.html', {
            'messages': request._messages,
            'DEFAULT_MESSAGE_LEVELS': messages.DEFAULT_LEVELS,
        })
        self.assertIn('alert-info', html)
        self.assertIn('fa-check-circle', html)
        self.assertIn('ส่งอนุมัติใบขอซื้อ RL16911002 ใหม่เรียบร้อยแล้ว', html)
