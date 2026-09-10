"""Year-scope filtering on the all-details procurement report."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from stock.models import Requisition
from stock.tests_all_details_report import _AllDetailsBase, URL_NAME

CURRENT_YEAR = timezone.now().year


class AllDetailsYearScopeTests(_AllDetailsBase):

    def setUp(self):
        super().setUp()
        # One RQ chain per year, backdated onto Requisition.created (the field
        # the scope filters on).
        self.years = [CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2,
                      CURRENT_YEAR - 3]
        for year in self.years:
            chain = self._build_chain(stage="RQ", rq_ref=f"REQ-{year}",
                                      product_code=f"P{year}",
                                      product_name="apple" if year % 2 == 0 else "banana")
            Requisition.objects.filter(id=chain["rq"].id).update(
                created=timezone.datetime(year, 6, 1).date())

    def _refs(self, params=None):
        resp = self.client.get(reverse(URL_NAME), params or {})
        return {r["requisition"].ref_no for r in resp.context["rows"]}, resp

    def test_default_scope_is_latest_three_years(self):
        refs, resp = self._refs()
        self.assertEqual(refs, {f"REQ-{y}" for y in self.years[:3]})
        self.assertEqual(resp.context["filter"].form["year_scope"].value(),
                         "last_3_years")

    def test_specific_year(self):
        year = CURRENT_YEAR - 3
        refs, _ = self._refs({"year_scope": str(year)})
        self.assertEqual(refs, {f"REQ-{year}"})

    def test_all_years(self):
        refs, _ = self._refs({"year_scope": "all"})
        self.assertEqual(refs, {f"REQ-{y}" for y in self.years})

    def test_search_combines_with_year_scope(self):
        apple_years = [y for y in self.years if y % 2 == 0]
        refs, _ = self._refs({"year_scope": "all", "search": "apple"})
        self.assertEqual(refs, {f"REQ-{y}" for y in apple_years})
        year = apple_years[0]
        refs, _ = self._refs({"year_scope": str(year), "search": "apple"})
        self.assertEqual(refs, {f"REQ-{year}"})
        refs, _ = self._refs({"year_scope": str(year), "search": "banana"})
        self.assertEqual(refs, set())

    def test_invalid_scope_falls_back_to_default(self):
        for bad in ("abc", "", "99999", "-1", "2026; DROP TABLE"):
            refs, resp = self._refs({"year_scope": bad})
            self.assertEqual(resp.status_code, 200, msg=bad)
            self.assertEqual(refs, {f"REQ-{y}" for y in self.years[:3]}, msg=bad)
            self.assertEqual(resp.context["filter"].form["year_scope"].value(),
                             "last_3_years", msg=bad)

    def test_year_scope_control_rendered_and_selected(self):
        resp = self.client.get(reverse(URL_NAME), {"year_scope": "all"})
        self.assertContains(resp, 'name="year_scope"')
        self.assertContains(resp, '<option value="all" selected>')
        self.assertContains(resp, f'<option value="{CURRENT_YEAR}" >')

    def test_pagination_preserves_year_scope_and_search(self):
        resp = self.client.get(reverse(URL_NAME),
                               {"year_scope": "all", "search": "apple", "page": "1"})
        self.assertContains(resp, "year_scope=all")

    def test_export_honours_year_scope(self):
        from stock.views import _all_details_export_queryset
        from django.test import RequestFactory
        request = RequestFactory().get(reverse(URL_NAME), {"year_scope": "all"})
        request.user = self.user
        request.session = self.client.session
        self.assertEqual(_all_details_export_queryset(request).count(), len(self.years))
        request = RequestFactory().get(reverse(URL_NAME))
        request.user = self.user
        request.session = self.client.session
        self.assertEqual(_all_details_export_queryset(request).count(), 3)


class AllDetailsYearScopeQueryCountTests(_AllDetailsBase):

    def _query_count(self, params):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse(URL_NAME), params)
        return len(ctx)

    def test_year_scope_is_a_where_clause_not_extra_queries(self):
        """Every scope renders the same rows here (all data is in the current
        year), so any difference in query count would come from the scope
        itself."""
        for i in range(3):
            chain = self._build_chain(stage="PO", rq_ref=f"REQ-Q{i}",
                                      pr_ref=f"PR-Q{i}", cp_ref=f"CP-Q{i}",
                                      po_ref=f"PO-Q{i}", product_code=f"Q{i}")
            Requisition.objects.filter(id=chain["rq"].id).update(
                created=timezone.datetime(CURRENT_YEAR, 6, 1).date())
        self.client.get(reverse(URL_NAME))  # warm up content-type/session caches
        default = self._query_count({})
        self.assertEqual(self._query_count({"year_scope": "all"}), default)
        self.assertEqual(self._query_count({"year_scope": str(CURRENT_YEAR)}), default)
