import re
from decimal import Decimal

from django.urls import reverse

from stock.views import _all_details_dashboard, _item_discount_amount
from stock.models import RequisitionItem
from stock.tests_all_details_report import _AllDetailsBase, URL_NAME

D = Decimal


class AllDetailsItemDiscountTests(_AllDetailsBase):
    """The 'ส่วนลด' dash-card totals the per-line discount of the scoped
    PurchaseOrderItems. `discount` is a free-text CharField holding either a
    plain amount or a "%" of that line's own quantity x unit_price, exactly as
    calculateUnitDiscount() treats it in the PO item templates."""

    def _discount_total(self, *lines):
        """Build one PO line per (discount, quantity, unit_price) tuple, then
        return the dashboard's po_item_discount over all of them."""
        for n, line in enumerate(lines):
            raw, qty, unit_price = line
            chain = self._build_chain(product_code="P%03d" % n, rq_ref="REQ-%03d" % n,
                                      po_ref="PO-%03d" % n, cp_ref="CP-%03d" % n)
            for po_item in chain["po_items"]:
                po_item.discount = raw
                po_item.quantity = None if qty is None else D(qty)
                po_item.unit_price = None if unit_price is None else D(unit_price)
                po_item.save()
        qs = RequisitionItem.objects.filter(requisit__branch_company__code="HO")
        return _all_details_dashboard(qs)["po_item_discount"]

    # ----- fixed discounts: the stored amount is used as-is -----
    def test_fixed_discount(self):
        self.assertEqual(self._discount_total(("100", "10", "200")), D("100"))

    def test_fixed_discount_with_decimals(self):
        self.assertEqual(self._discount_total(("100.50", "1", "200")), D("100.50"))

    def test_fixed_discount_with_thousand_separator(self):
        self.assertEqual(self._discount_total(("1,234.50", "1", "200")), D("1234.50"))

    def test_fixed_discount_zero(self):
        self.assertEqual(self._discount_total(("0", "10", "200")), D("0"))

    # ----- percentage discounts: base = quantity x unit_price -----
    def test_percentage_discount(self):
        # 10 x 200 = 2,000 base; 5% -> 100
        self.assertEqual(self._discount_total(("5%", "10", "200")), D("100.00"))

    def test_percentage_discount_ten_percent(self):
        # 5 x 500 = 2,500 base; 10% -> 250
        self.assertEqual(self._discount_total(("10%", "5", "500")), D("250.00"))

    def test_percentage_zero(self):
        self.assertEqual(self._discount_total(("0%", "10", "200")), D("0"))

    def test_percentage_hundred_is_the_whole_base(self):
        self.assertEqual(self._discount_total(("100%", "10", "200")), D("2000.00"))

    def test_percentage_with_spaces_and_decimals(self):
        # 10 x 200 = 2,000 base; 2.5% -> 50
        self.assertEqual(self._discount_total((" 2.5% ", "10", "200")), D("50.00"))

    # ----- per-item, not off the combined total -----
    def test_multiple_percentage_items_are_summed_per_line(self):
        # 10x200 @5% = 100 | 5x100 @10% = 50 | 2x500 @20% = 200
        self.assertEqual(
            self._discount_total(("5%", "10", "200"), ("10%", "5", "100"),
                                 ("20%", "2", "500")),
            D("350.00"))

    def test_mixed_fixed_and_percentage(self):
        # 10x200 @5% = 100 | 5x100 @"100" = 100 | 2x500 @10% = 100
        self.assertEqual(
            self._discount_total(("5%", "10", "200"), ("100", "5", "100"),
                                 ("10%", "2", "500")),
            D("300.00"))

    # ----- edge cases -----
    def test_zero_quantity_percentage_is_zero(self):
        self.assertEqual(self._discount_total(("10%", "0", "200")), D("0"))

    def test_zero_unit_price_percentage_is_zero(self):
        self.assertEqual(self._discount_total(("10%", "10", "0")), D("0"))

    def test_null_quantity_percentage_is_zero(self):
        self.assertEqual(self._discount_total(("10%", None, "200")), D("0"))

    def test_null_unit_price_percentage_is_zero(self):
        self.assertEqual(self._discount_total(("10%", "10", None)), D("0"))

    def test_large_values(self):
        # 1,000 x 9,999.99 = 9,999,990 base; 15% -> 1,499,998.50
        self.assertEqual(self._discount_total(("15%", "1000", "9999.99")),
                         D("1499998.50"))

    def test_no_discount_data_totals_zero(self):
        self.assertEqual(self._discount_total(), D("0"))

    # ----- invalid free-text entries contribute 0 -----
    def test_invalid_entries_contribute_zero(self):
        for raw in [None, "", "   ", "ไม่มี", "abc", "NaN", "nan", "INF", "inf",
                    "Infinity", "-Infinity", "-inf", "%", "abc%", "NaN%", "inf%"]:
            with self.subTest(discount=raw):
                amount = _item_discount_amount(raw, D("10"), D("200"))
                self.assertEqual(amount, D("0"))
                self.assertTrue(amount.is_finite())

    def test_invalid_entries_contribute_zero_through_the_dashboard(self):
        self.assertEqual(
            self._discount_total(("NaN", "10", "200"), ("inf", "10", "200"),
                                 ("-Infinity", "10", "200"), ("abc", "10", "200"),
                                 ("", "10", "200"), ("   ", "10", "200"),
                                 (None, "10", "200"), ("NaN%", "10", "200")),
            D("0"))

    # ----- a bad row must not poison the valid ones -----
    def test_nan_row_does_not_discard_valid_rows(self):
        # NaN -> 0 | 5x100 @10% = 50
        self.assertEqual(self._discount_total(("NaN", "10", "200"),
                                              ("10%", "5", "100")), D("50.00"))

    def test_mixed_invalid_fixed_and_percentage(self):
        # NaN -> 0 | 10x200 @5% = 100 | fixed 100
        self.assertEqual(
            self._discount_total(("NaN", "1", "1"), ("5%", "10", "200"),
                                 ("100", "1", "1")),
            D("200.00"))

    def test_infinity_row_does_not_discard_valid_rows(self):
        self.assertEqual(self._discount_total(("Infinity", "10", "200"),
                                              ("250.00", "1", "1")), D("250.00"))

    # ----- what the card actually renders -----
    def _rendered_cards(self):
        res = self.client.get(reverse(URL_NAME))
        self.assertEqual(res.status_code, 200)
        pairs = re.findall(r'dash-card__label">([^<]*)</div>\s*'
                           r'<div class="dash-card__value">([^<]*)</div>',
                           res.content.decode())
        self.assertTrue(pairs, "no dash-cards rendered")
        return {label.strip(): value.strip() for label, value in pairs}

    def test_dash_card_shows_calculated_percentage_discount(self):
        self._discount_total(("NaN", "10", "200"), ("5%", "10", "200"),
                             ("100", "5", "100"))
        cards = self._rendered_cards()
        self.assertEqual(cards["ส่วนลด"], "200.00")

    def test_dash_card_never_renders_nan_or_infinity(self):
        self._discount_total(("NaN", "10", "200"), ("inf", "1", "1"))
        cards = self._rendered_cards()
        self.assertEqual(cards["ส่วนลด"], "0.00")
        for label, value in cards.items():
            self.assertNotIn("nan", value.lower(), label)
            self.assertNotIn("inf", value.lower(), label)

    def test_bill_level_discount_card_is_unaffected(self):
        # 'ส่วนลดท้ายบิล' comes from the PO/CPD headers, not the item lines.
        self._discount_total(("5%", "10", "200"))
        cards = self._rendered_cards()
        self.assertEqual(cards["ส่วนลดท้ายบิล"], "0.00")
        self.assertEqual(cards["ส่วนลด"], "100.00")
