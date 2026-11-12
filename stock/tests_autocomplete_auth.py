from django.test import TestCase
from django.urls import reverse


class AutocompleteRequiresLoginTestCase(TestCase):
    """ค้นหา/autocomplete ต้อง login ก่อน ไม่งั้น redirect ไปหน้า signIn"""

    URLS = [
        ('product_search', {'q': 'abc'}),
        ('car_search', {'q': 'abc'}),
        ('autocompalteDistributor', {'term': 'abc', 'rich': '1'}),
        ('autocompalte_maintenance', {'term': 'abc'}),
    ]

    def test_anonymous_is_redirected_to_sign_in(self):
        sign_in = reverse('signIn')
        for name, params in self.URLS:
            with self.subTest(name = name):
                resp = self.client.get(reverse(name), params, HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
                self.assertEqual(resp.status_code, 302)
                self.assertTrue(resp['Location'].startswith(sign_in))
