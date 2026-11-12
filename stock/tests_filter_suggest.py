import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from stock.filter_suggest import SuggestInput, filter_suggest_response
from stock.filters import (ComparisonPriceFilter, PurchaseOrderFilter, PurchaseOrderItemFilter,
                           PurchaseRequisitionFilter, RequisitionFilter)
from stock.models import (
    BaseAddress, BaseBranchCompany, ComparisonPrice, ComparisonPriceItem, Distributor, Product,
    PurchaseRequisition, Requisition, RequisitionItem, UserProfile,
)

#ช่องกรองข้อความที่ต้องมี dropdown ค่าแนะนำ ในแต่ละ FilterSet ของหน้ารายการ
SUGGEST_FIELDS = {
    RequisitionFilter: ['name', 'ref_no'],
    PurchaseRequisitionFilter: ['ref_no', 'requisition__name', 'item_product_name', 'item_product_id',
                                'item_machine', 'item_rq_note'],
    PurchaseOrderFilter: ['distributor', 'cp_ref_no', 'pr_ref_no', 'item_machine', 'item_rq_note',
                          'item_product_name', 'item_product_id', 'item_product_id_from', 'item_product_id_to',
                          'distri_id', 'ref_no'],
    PurchaseOrderItemFilter: ['item_product_id_from', 'item_product_id_to', 'item_product_name', 'item_machine',
                              'item_rq_note', 'distri_id', 'distributor', 'po_ref_no', 'cp_ref_no', 'pr_ref_no'],
    ComparisonPriceFilter: ['select_bidder', 'ref_no', 'item_product_name', 'item_product_id', 'pr_ref_no'],
}


class _Fixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        cls.address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        cls.user = User.objects.create_user(username="suggester", password="pw",
                                            first_name="สมชาย", last_name="ใจดี")
        UserProfile.objects.create(user=cls.user).branch_company.add(cls.branch)
        cls.shop = Distributor.objects.create(id="D-001", name="ศรีพานิช")
        cls.other_shop = Distributor.objects.create(id="D-002", name="ศรีสยาม")
        cls.rq = Requisition.objects.create(
            name=cls.user, chief_approve_user_name=cls.user, supplies_approve_user_name=cls.user,
            branch_company=cls.branch, address_company=cls.address, ref_no="RQ-001", pr_ref_no="PR-001",
            note="เปลี่ยนลูกปืน\nเครื่องโม่หิน " + "ก" * 200)
        cls.product = Product.objects.create(id="P-100", name="ตลับลูกปืน 6205", slug="p-100")
        cls.rq_item = RequisitionItem.objects.create(requisition_id=cls.rq.id, requisit=cls.rq, product=cls.product,
                                                     product_name="ตลับลูกปืน 6205", machine="โม่หิน 1")
        #ใบที่หน้า viewComparePricePO แสดง (ยังไม่ออก PO) และใบที่ไม่แสดง (ออก PO แล้ว)
        cls.cp_open = cls._cp("CM-001", cls.shop, po_ref_no="")
        cls.cp_done = cls._cp("CM-002", cls.other_shop, po_ref_no="PO-9")
        ComparisonPriceItem.objects.create(cp=cls.cp_open.id, item=cls.rq_item)

    @classmethod
    def _cp(cls, ref_no, shop, po_ref_no):
        return ComparisonPrice.objects.create(organizer=cls.user, branch_company=cls.branch,
                                              address_company=cls.address, ref_no=ref_no,
                                              select_bidder=shop, po_ref_no=po_ref_no, is_draft=False)


class SuggestWidgetsTestCase(TestCase):
    def test_every_text_filter_on_list_pages_has_suggest_widget(self):
        for filterset, fields in SUGGEST_FIELDS.items():
            for name in fields:
                with self.subTest(filterset=filterset.__name__, field=name):
                    self.assertIsInstance(filterset.base_filters[name].extra.get('widget'), SuggestInput)
                    self.assertIn('data-suggest=', str(filterset().form[name]))

    def test_suggest_paths_are_valid_on_empty_db(self):
        """path ของทุกช่องต้อง query ได้จริง (สะกดผิด/ไม่มี relation จะ FieldError)"""
        factory = RequestFactory()
        for filterset, fields in SUGGEST_FIELDS.items():
            for name in fields:
                with self.subTest(filterset=filterset.__name__, field=name):
                    request = factory.get('/', {'_suggest': name, 'q': 'x'})
                    response = filter_suggest_response(request, filterset(request.GET))
                    self.assertEqual(response.status_code, 200)


class ComparisonPricePageSuggestTestCase(_Fixture):
    """หน้า viewComparePricePO: ค่าแนะนำมาจากใบที่หน้านี้แสดงเท่านั้น และเลือกแล้วกรองเจอเสมอ"""

    def setUp(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['company_code'] = 'HO'   # RequireCompanyCodeMiddleware
        session.save()
        self.url = reverse('viewComparePricePO')

    def suggest(self, field, q):
        response = self.client.get(self.url, {'_suggest': field, 'q': q})
        self.assertEqual(response.status_code, 200)
        return response.json()['results']

    def test_only_documents_shown_on_this_page(self):
        self.assertEqual([r['id'] for r in self.suggest('ref_no', 'CM')], ['CM-001'])
        self.assertEqual([r['id'] for r in self.suggest('select_bidder', 'สรี')], ['ศรีพานิช'])

    def test_every_suggestion_filters_to_a_result(self):
        for field, q in (('ref_no', 'CM'), ('select_bidder', 'ศรี'), ('item_product_name', 'ลูกปืน'),
                         ('item_product_id', 'ลูกปืน'), ('pr_ref_no', 'PR')):
            results = self.suggest(field, q)
            with self.subTest(field=field):
                self.assertTrue(results)
            for r in results:
                with self.subTest(field=field, value=r['id']):
                    page = self.client.get(self.url, {field: r['id']})
                    self.assertEqual([cp.ref_no for cp in page.context['cps']], ['CM-001'])

    def test_product_id_shows_name_but_sends_id(self):
        r = self.suggest('item_product_id', 'ลูกปืน')[0]
        self.assertEqual(r['id'], 'P-100')
        self.assertIn('ตลับลูกปืน 6205', r['text'])

    def test_empty_term_and_unknown_field(self):
        self.assertEqual(self.suggest('ref_no', '  '), [])
        response = self.client.get(self.url, {'_suggest': 'organizer', 'q': 'x'})
        self.assertEqual(response.status_code, 404)

    def test_page_renders_suggest_inputs_and_script(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn('data-suggest=', html)
        self.assertIn('window.loadSelect2Once', html)
        self.assertIn('_suggest: field', html)


class PurchaseRequisitionSuggestTestCase(_Fixture):
    """ใบขอซื้อ: ผู้ขอเบิก / หมายเหตุหลายบรรทัด / ระบบงาน"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.pr = PurchaseRequisition.objects.create(ref_no="PR-001", requisition=cls.rq,
                                                    branch_company=cls.branch, address_company=cls.address)
        cls.base = PurchaseRequisition.objects.filter(pk=cls.pr.pk)

    def suggest(self, field, q):
        request = RequestFactory().get('/', {'_suggest': field, 'q': q})
        response = filter_suggest_response(request, PurchaseRequisitionFilter(request.GET, queryset=self.base))
        return json.loads(response.content)['results']

    def assert_filters_to_pr(self, field, value):
        qs = PurchaseRequisitionFilter({field: value}, queryset=self.base).qs
        self.assertEqual(list(qs), [self.pr])

    def test_requisition_user_full_name(self):
        results = self.suggest('requisition__name', 'ใจ')
        self.assertEqual([r['id'] for r in results], ['สมชาย ใจดี'])
        self.assert_filters_to_pr('requisition__name', 'สมชาย ใจดี')

    def test_multiline_note_sends_first_line(self):
        results = self.suggest('item_rq_note', 'โม่ ลูกปืน')
        self.assertEqual(results[0]['id'], 'เปลี่ยนลูกปืน')
        self.assertTrue(results[0]['text'].startswith('เปลี่ยนลูกปืน เครื่องโม่หิน'))
        self.assertLessEqual(len(results[0]['text']), 120)
        self.assert_filters_to_pr('item_rq_note', results[0]['id'])

    def test_machine_suggest_and_filter(self):
        #เดิมช่องนี้กรองจาก requisition__machine ซึ่งไม่มีอยู่จริง -> FieldError
        results = self.suggest('item_machine', 'โม่')
        self.assertEqual([r['id'] for r in results], ['โม่หิน 1'])
        self.assert_filters_to_pr('item_machine', 'โม่หิน 1')
