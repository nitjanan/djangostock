from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from stock.models import BaseBranchCompany


class SignInCsrfTestCase(TestCase):
    """หน้า login กัน CSRF 403 ที่เกิดจากการส่งฟอร์ม login ซ้ำหลัง login สำเร็จแล้ว"""

    @classmethod
    def setUpTestData(cls):
        BaseBranchCompany.objects.create(id="SCF", code="SCF", name="SCF Co")
        cls.user = User.objects.create_user(username="csrf_user", password="pass-1234")

    def _login(self, client):
        client.force_login(self.user)
        session = client.session
        session["company_code"] = "SCF"
        session.save()

    def test_signin_page_is_not_cached(self):
        resp = self.client.get(reverse("signIn"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("no-cache", resp["Cache-Control"])
        self.assertIn("no-store", resp["Cache-Control"])

    def test_authenticated_user_redirected_from_signin(self):
        self._login(self.client)
        resp = self.client.get(reverse("signIn"))
        self.assertRedirects(resp, reverse("home"), fetch_redirect_response=False)

    def test_stale_token_on_signin_after_login_goes_home(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("signIn"))
        self._login(client)  # login แล้ว token เปลี่ยน ฟอร์มเก่ายังถือ token เดิม
        resp = client.post(reverse("signIn"), {
            "username": "csrf_user", "password": "pass-1234",
            "csrfmiddlewaretoken": "x" * 64,
        })
        self.assertRedirects(resp, reverse("home"), fetch_redirect_response=False)

    def test_stale_token_on_signin_when_logged_out_back_to_signin(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("signIn"))
        resp = client.post(reverse("signIn"), {
            "username": "csrf_user", "password": "pass-1234",
            "csrfmiddlewaretoken": "x" * 64,
        })
        self.assertRedirects(resp, reverse("signIn"), fetch_redirect_response=False)

    def test_stale_token_on_other_page_shows_friendly_page(self):
        client = Client(enforce_csrf_checks=True)
        self._login(client)
        client.get(reverse("signIn"))  # ได้ cookie CSRF
        resp = client.post(reverse("signOut"), {"csrfmiddlewaretoken": "x" * 64},
                           HTTP_REFERER="http://testserver/some/page")
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, "หน้านี้หมดอายุแล้ว", status_code=403)
        self.assertContains(resp, "http://testserver/some/page", status_code=403)

    def test_foreign_referer_not_used_as_back_link(self):
        client = Client(enforce_csrf_checks=True)
        self._login(client)
        resp = client.post(reverse("signOut"), {"csrfmiddlewaretoken": "x" * 64},
                           HTTP_REFERER="https://evil.example.com/")
        self.assertEqual(resp.status_code, 403)
        self.assertNotContains(resp, "evil.example.com", status_code=403)
