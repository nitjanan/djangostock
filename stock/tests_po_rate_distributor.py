from django.test import TestCase, override_settings
from django.urls import reverse

from stock.models import RateDistributor
from stock.tests_po_save_draft import PurchaseOrderSaveDraftTestCase as _DraftCase


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PurchaseOrderRateDistributorTestCase(TestCase):
    """ประเมินผู้จำหน่ายในหน้า purchaseOrderItem/edit: บันทึกแล้วเปิดมาใหม่ต้องเห็นดาวเดิม"""

    #ใช้ข้อมูลตั้งต้นและ helper เดียวกับเทสต์บันทึกแบบร่างใบสั่งซื้อ (ไม่รันเทสต์ของคลาสนั้นซ้ำ)
    setUp = _DraftCase.setUp
    _create_po = _DraftCase._create_po
    _price_data = _DraftCase._price_data
    _post_edit = _DraftCase._post_edit

    def _edit_url(self, po):
        return reverse('editPOItem', kwargs={'po_id': po.id, 'isFromPR': 'True', 'isReApprove': 'False'})

    def test_draft_save_keeps_rating_and_reopen_shows_stars(self):
        po, item = self._create_po(with_item=True, is_draft=True)
        response = self._post_edit(
            po, item, save_draft=True, price_rate=4, quantity_rate=3, service_rate=4, safety_rate=3,
        )
        self.assertEqual(response.status_code, 302)
        rate = RateDistributor.objects.get(po=po)
        self.assertEqual(rate.distributor_id, self.distributor.id)
        self.assertEqual(
            (rate.price_rate, rate.quantity_rate, rate.service_rate, rate.safety_rate), (4, 3, 4, 3)
        )

        html = self.client.get(self._edit_url(po)).content.decode('utf-8')
        self.assertIn('$(\'input[name="rate-price"][value=\'+"4"+\']\')', html)
        self.assertIn('$(\'input[name="rate-quantity"][value=\'+"3"+\']\')', html)
        self.assertIn("tmp_dist = '%s'" % self.distributor.id, html)

    def test_focusout_resets_stars_only_when_distributor_changes(self):
        #เดิม focusout ช่องผู้จำหน่ายเรียก resetRate() ทุกครั้งที่ยังไม่เคยประเมิน ดาวที่กดไว้จึงกลายเป็น 0
        po, _ = self._create_po(with_item=True, is_draft=True)
        html = self.client.get(self._edit_url(po)).content.decode('utf-8')
        start = html.index('function searchDataDistributor')
        body = html[start:html.index('function setDataDistributor', start)]
        self.assertIn('if(distChanged)', body)
