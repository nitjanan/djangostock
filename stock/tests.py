from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
import datetime
from stock.models import BaseBranchCompany, BaseVatType, BaseAddress, PurchaseOrder, RequisitionItem, PurchaseOrderItem, BaseUnit, ComparisonPrice, ComparisonPriceDistributor, Distributor, BaseCredit, BaseApproveStatus, BasePOType, BranchCompanyBaseAdress, RateDistributor, CarLogbook, BaseCar

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


class CreatePOFromComparisonPriceTestCase(TestCase):
    def setUp(self):
        from stock.models import UserProfile
        from django.contrib.auth.models import Group

        self.client = Client()
        self.user = User.objects.create_user(username='tester_cp', password='password')
        
        # Assign user to group "ผู้อนุมัติ" so that PurchaseOrderFromComparisonPriceForm.approver_user has options
        approver_group, _ = Group.objects.get_or_create(name='ผู้อนุมัติ')
        self.user.groups.add(approver_group)
        self.client.login(username='tester_cp', password='password')

        # Setup session company_code
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        # Create models
        self.branch = BaseBranchCompany.objects.create(
            id="1",
            code="HO",
            name="Head Office"
        )
        self.vat_type = BaseVatType.objects.create(
            id="1",
            name="Vat 7%"
        )
        self.address = BaseAddress.objects.create(
            name_th="Test Company",
            address="123 Test St"
        )
        # Create BranchCompanyBaseAdress
        self.bc_address = BranchCompanyBaseAdress.objects.create(
            branch_company=self.branch,
            address=self.address
        )
        self.credit = BaseCredit.objects.create(
            name="Cash"
        )
        self.distributor = Distributor.objects.create(
            id="dist_01",
            name="Test Distributor",
            credit=self.credit,
            vat_type=self.vat_type
        )
        self.po_type = BasePOType.objects.create(
            id="po_type_1",
            name="Standard PO"
        )
        self.approve_status = BaseApproveStatus.objects.create(
            id=1,
            name="Pending"
        )
        # Create UserProfile for user
        self.profile = UserProfile.objects.create(user=self.user)
        self.profile.branch_company.add(self.branch)

        # Create ComparisonPrice
        self.cp = ComparisonPrice.objects.create(
            organizer=self.user,
            select_bidder=self.distributor,
            address_company=self.address,
            branch_company=self.branch
        )
        # Set cp.created and cp.select_bidder_update to test select_bidder_update copying
        self.cp_created_date = datetime.date(2026, 6, 15)
        self.cp_select_bidder_update = datetime.date(2026, 6, 20)
        ComparisonPrice.objects.filter(id=self.cp.id).update(
            created=self.cp_created_date,
            select_bidder_update=self.cp_select_bidder_update
        )
        self.cp.refresh_from_db()

        # Create ComparisonPriceDistributor
        self.cpd = ComparisonPriceDistributor.objects.create(
            cp=self.cp,
            distributor=self.distributor,
            credit=self.credit,
            vat_type=self.vat_type,
            total_price=100.00,
            amount=107.00
        )

    def test_create_po_sets_created_from_select_bidder_update(self):
        url = reverse('createPOFromComparisonPrice', kwargs={'cp_id': self.cp.id})
        
        post_data = {
            'cp': self.cp.id,
            'shipping': 'EMS',
            'address_company': self.address.id,
            'approver_user': self.user.id,
            'due_receive_update': '2026-07-20',
            'po_type': self.po_type.id,
            
            # RateDistributorForm fields
            'distributor': self.distributor.id,
            'price_rate': 5,
            'quantity_rate': 5,
            'service_rate': 5,
            'safety_rate': 5,
            'counsel': 'Excellent service'
        }
        
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify PurchaseOrder is created and created date matches select_bidder_update
        po = PurchaseOrder.objects.get(cp=self.cp)
        self.assertEqual(po.created, self.cp_select_bidder_update)
        
        # Verify po.ref_no runs by the created date (HO + Buddhist Year 69 + Month 06 + 001)
        self.assertEqual(po.ref_no, 'HO6906001')

    def test_create_po_falls_back_to_comparison_price_created_if_select_bidder_update_null(self):
        # Set select_bidder_update to None
        ComparisonPrice.objects.filter(id=self.cp.id).update(select_bidder_update=None)
        
        url = reverse('createPOFromComparisonPrice', kwargs={'cp_id': self.cp.id})
        
        post_data = {
            'cp': self.cp.id,
            'shipping': 'EMS',
            'address_company': self.address.id,
            'approver_user': self.user.id,
            'due_receive_update': '2026-07-20',
            'po_type': self.po_type.id,
            
            # RateDistributorForm fields
            'distributor': self.distributor.id,
            'price_rate': 5,
            'quantity_rate': 5,
            'service_rate': 5,
            'safety_rate': 5,
            'counsel': 'Excellent service'
        }
        
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify PurchaseOrder created date falls back to cp.created
        po = PurchaseOrder.objects.get(cp=self.cp)
        self.assertEqual(po.created, self.cp_created_date)


class CarLogbookMileDecimalTestCase(TestCase):
    def setUp(self):
        self.branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.address = BaseAddress.objects.create(name_th="Test Company", address="123 Test St")
        BranchCompanyBaseAdress.objects.create(branch_company=self.branch, address=self.address)

    def test_case1_existing_integer_value(self):
        cl = CarLogbook.objects.create(
            branch_company=self.branch, address_company=self.address,
            mile_start=1000, mile_end=1100,
        )
        self.assertEqual(cl.diff_mile, Decimal("100.00"))

    def test_case2_decimal_value(self):
        cl = CarLogbook.objects.create(
            branch_company=self.branch, address_company=self.address,
            mile_start=Decimal("1000.25"), mile_end=Decimal("1100.75"),
        )
        self.assertEqual(cl.diff_mile, Decimal("100.50"))

    def test_case3_small_decimal_difference(self):
        cl = CarLogbook.objects.create(
            branch_company=self.branch, address_company=self.address,
            mile_start=Decimal("100.10"), mile_end=Decimal("100.25"),
        )
        self.assertEqual(cl.diff_mile, Decimal("0.15"))

    def test_case4_zero(self):
        cl = CarLogbook.objects.create(
            branch_company=self.branch, address_company=self.address,
            mile_start=Decimal("0.00"), mile_end=Decimal("0.00"),
        )
        self.assertEqual(cl.diff_mile, Decimal("0.00"))

    def test_case5_null_handling(self):
        cl = CarLogbook.objects.create(
            branch_company=self.branch, address_company=self.address,
            mile_start=None, mile_end=None,
        )
        self.assertIsNone(cl.diff_mile)
        self.assertIsNone(cl.mile_start_job1)
        self.assertIsNone(cl.mile_end_job1)
        self.assertIsNone(cl.diff_mile_job1)

    def test_job_mile_fields_accept_decimal_and_compute_diff(self):
        cl = CarLogbook.objects.create(
            branch_company=self.branch, address_company=self.address,
            mile_start_job1=Decimal("500.50"), mile_end_job1=Decimal("600.75"),
        )
        self.assertEqual(cl.diff_mile_job1, Decimal("100.25"))
        # auto-fill: mile_start should default from mile_start_job1 when mile_start is None
        self.assertEqual(cl.mile_start, Decimal("500.50"))

    def test_max_digits_precision_field_definition(self):
        field = CarLogbook._meta.get_field("mile_start")
        self.assertEqual(field.max_digits, 8)
        self.assertEqual(field.decimal_places, 2)
        for name in [
            "mile_start", "mile_end", "diff_mile",
            "mile_start_job1", "mile_end_job1", "diff_mile_job1",
            "mile_start_job2", "mile_end_job2", "diff_mile_job2",
            "mile_start_job3", "mile_end_job3", "diff_mile_job3",
            "mile_start_job4", "mile_end_job4", "diff_mile_job4",
            "mile_start_job5", "mile_end_job5", "diff_mile_job5",
            "mile_start_job6", "mile_end_job6", "diff_mile_job6",
        ]:
            f = CarLogbook._meta.get_field(name)
            self.assertEqual(f.__class__.__name__, "DecimalField", name)

