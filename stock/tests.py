from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from stock.models import BaseBranchCompany, BaseVatType, BaseAddress, PurchaseOrder, RequisitionItem, PurchaseOrderItem, BaseUnit

class PurchaseOrderItemDoubleSubmitTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create standard user and login
        self.user = User.objects.create_user(username='tester', password='password')
        self.client.login(username='tester', password='password')
        
        # Setup session company_code
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()
        
        # Create required branch company
        self.branch = BaseBranchCompany.objects.create(
            id="1",
            code="HO",
            name="Head Office"
        )
        
        # Create required vat type
        self.vat_type = BaseVatType.objects.create(
            id="1",
            name="Vat 7%"
        )

        # Create address
        self.address = BaseAddress.objects.create(
            name_th="Test Company",
            address="123 Test St"
        )

        # Create unit
        self.unit = BaseUnit.objects.create(
            name="ชิ้น"
        )
        
        # Create purchase order
        self.po = PurchaseOrder.objects.create(
            vat_type=self.vat_type,
            ref_no="PO-TEST-001",
            total_price=50.00,
            amount=50.00,
            address_company=self.address
        )
        
        # Create requisition item
        self.req_item = RequisitionItem.objects.create(
            requisition_id=1,
            product_name="Test Item 1",
            quantity=5,
            quantity_pr=5
        )

    def test_create_po_item_prevent_double_submit(self):
        url = reverse('createPOItem', kwargs={'po_id': self.po.id})
        
        # Construct form and formset POST data
        post_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-item': self.req_item.id,
            'form-0-quantity': '5.0000',
            'form-0-unit_price': '10.0000',
            'form-0-price': '50.00',
            'form-0-unit': self.unit.id,
            'total_price': '50.00',
            'discount': '0.00',
            'total_after_discount': '50.00',
            'vat': '0.00',
            'amount': '50.00',
            'freight': '0.00',
            'note': '',
            'delivery': ''
        }
        
        # Send first POST request (creation)
        response1 = self.client.post(url, data=post_data)
        if response1.status_code != 302:
            if 'formset' in response1.context:
                errors_str = str(response1.context['formset'].errors).encode('ascii', errors='backslashreplace').decode('ascii')
                print("Formset errors:", errors_str)
            if 'price_form' in response1.context:
                errors_str = str(response1.context['price_form'].errors).encode('ascii', errors='backslashreplace').decode('ascii')
                print("Price form errors:", errors_str)
        self.assertEqual(response1.status_code, 302)  # Should redirect
        
        # Verify 1 item is created
        items_count = PurchaseOrderItem.objects.filter(po=self.po).count()
        self.assertEqual(items_count, 1)
        
        # Send second POST request simulating double submit (with same data and no IDs)
        response2 = self.client.post(url, data=post_data)
        self.assertEqual(response2.status_code, 302)  # Should redirect
        
        # Verify count is STILL 1 (no duplicate item created)
        items_count_after = PurchaseOrderItem.objects.filter(po=self.po).count()
        self.assertEqual(items_count_after, 1)
