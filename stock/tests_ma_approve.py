from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from stock.models import BaseBranchCompany, BaseAddress, BranchCompanyBaseAdress, Maintenance


class MAApproveNoteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='approver', password='password')
        self.client.login(username='approver', password='password')
        # RequireCompanyCodeMiddleware จะ logout ถ้า session ไม่มี company_code
        session = self.client.session
        session['company_code'] = 'HO'
        session.save()

        branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        address = BaseAddress.objects.create(name_th="Test Co", address="1 Test Rd")
        BranchCompanyBaseAdress.objects.create(branch_company=branch, address=address)

        self.ma = Maintenance.objects.create(branch_company=branch, approve_status='ขออนุมัติซ่อมบำรุง')
        self.url = reverse('editMAApprove', args=[self.ma.id, 1])

    def test_approve_saves_note(self):
        response = self.client.post(self.url, {'status': 'อนุมัติ', 'approve_note': '  ให้ซ่อมด่วน  '})
        self.assertRedirects(response, reverse('viewMAApprove'), fetch_redirect_response=False)

        self.ma.refresh_from_db()
        self.assertEqual(self.ma.approve_status, 'อนุมัติซ่อมบำรุง')
        self.assertEqual(self.ma.approve_name_id, self.user.id)
        self.assertEqual(self.ma.approve_note, 'ให้ซ่อมด่วน')

    def test_approve_without_note_saves_none(self):
        self.client.post(self.url, {'status': 'อนุมัติ', 'approve_note': '   '})

        self.ma.refresh_from_db()
        self.assertEqual(self.ma.approve_status, 'อนุมัติซ่อมบำรุง')
        self.assertIsNone(self.ma.approve_note)

    def test_approve_without_note_field_still_works(self):
        # หน้า edit เดิมไม่มีช่องความคิดเห็น ต้องยังอนุมัติได้
        self.client.post(self.url, {'status': 'อนุมัติ'})

        self.ma.refresh_from_db()
        self.assertEqual(self.ma.approve_status, 'อนุมัติซ่อมบำรุง')
        self.assertIsNone(self.ma.approve_note)
