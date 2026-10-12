from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from stock.models import (
    BaseBranchCompany, DistributorCandidate, DistributorForm, DistributorRule, DistributorRuleGroup, UserProfile,
)


class DistributorRulePageTestCase(TestCase):
    """หน้าจัดการหลักเกณฑ์ใบขอเพิ่ม Supplier (เฉพาะกลุ่ม ApproveDistributor)"""

    def setUp(self):
        branch = BaseBranchCompany.objects.create(id="1", code="HO", name="Head Office")
        self.approver = User.objects.create_user(username="approver", password="pw")
        self.approver.groups.add(Group.objects.get_or_create(name="ApproveDistributor")[0])
        self.user = User.objects.create_user(username="user", password="pw")
        for u in (self.approver, self.user):
            UserProfile.objects.create(user=u).branch_company.add(branch)
        self.login(self.approver)

    def login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session["company_code"] = "HO"
        session.save()

    def rule(self, code):
        return DistributorRule.objects.get(code=code)

    def post(self, name, *args, data=None):
        return self.client.post(reverse(name, args=args), data or {})

    def save_rule(self, rule=None, **data):
        if rule is None:
            return self.post("distributorRuleCreate", data=data)
        return self.post("distributorRuleEdit", rule.pk, data=data)

    def requirement(self, code):
        """ข้อความในคอลัมน์ "ต้องผ่านไหม" ของหน้ารายการ"""
        rows = self.client.get(reverse("distributorRuleList")).context["rows"]
        return next(row["requirement"] for row in rows if row["rule"].code == code)

    # ----- หน้ารายการ -----

    def test_list_tree_and_requirement_text(self):
        response = self.client.get(reverse("distributorRuleList"))
        rows = response.context["rows"]
        codes = [row["rule"].code for row in rows]
        self.assertEqual(codes[codes.index("9"):codes.index("9") + 3], ["9", "9.1", "9.2"])
        self.assertEqual(self.requirement("1"), "บังคับ")
        self.assertEqual(self.requirement("3"), "")
        self.assertEqual(self.requirement("8"), "บังคับ (ใช้ ข้อ 9 แทนได้)")
        self.assertEqual(self.requirement("9.1"), "นับรวมในข้อ 9")
        # คำว่า "กลุ่มเกณฑ์บังคับ" ไม่โผล่ในหน้าแล้ว
        self.assertNotContains(response, "กลุ่มเกณฑ์บังคับ")

    def test_only_approvers(self):
        self.login(self.user)
        for name, args in (("distributorRuleList", ()), ("distributorRuleCreate", ()), ("distributorRuleEdit", (self.rule("1").pk,))):
            self.assertRedirects(self.client.get(reverse(name, args=args)), reverse("distributorCandidateList"), fetch_redirect_response=False)
        self.post("distributorRuleToggle", self.rule("1").pk)
        self.post("distributorRuleDelete", self.rule("3").pk)
        self.assertTrue(self.rule("1").is_active)
        self.assertTrue(DistributorRule.objects.filter(code="3").exists())

    # ----- เพิ่มข้อ -----

    def test_new_main_rule_suggests_next_code(self):
        response = self.client.get(reverse("distributorRuleCreate"))
        self.assertEqual(response.context["form"]["code"].value(), "12")
        self.assertEqual(response.context["form"]["kind"].value(), "main")

    def test_new_child_from_list_button(self):
        nine = self.rule("9")
        response = self.client.get(reverse("distributorRuleCreate") + f"?parent={nine.pk}")
        form = response.context["form"]
        self.assertEqual((form["kind"].value(), form["code"].value()), ("child", "9.3"))
        self.assertContains(response, f'value="{nine.pk}" data-code="9.3"')

        self.save_rule(kind="child", parent=nine.pk, code="9.3", name="ผู้ขนส่ง")
        new = self.rule("9.3")
        self.assertEqual(new.parent, nine)
        self.assertIsNone(new.mandatory_group)
        self.assertEqual(new.order, self.rule("9.2").order + 10)

    def test_create_not_required(self):
        response = self.save_rule(kind="main", code="12", name="ข้อใหม่", requirement="no")
        new = self.rule("12")
        self.assertRedirects(response, reverse("distributorRuleList") + f"#rule-{new.pk}", fetch_redirect_response=False)
        self.assertIsNone(new.mandatory_group)
        self.assertTrue(new.is_active)
        # ข้อใหม่ขึ้นในฟอร์มและต้องตอบก่อนส่ง
        c = DistributorCandidate.objects.create(place_source="osm", place_id="node/1", name="x")
        self.assertIn("12", [r.code for r in c.evaluate()["missing"]])

    def test_create_required_makes_own_group(self):
        groups_before = DistributorRuleGroup.objects.count()
        self.save_rule(kind="main", code="12", name="มีใบรับรอง", requirement="yes")
        group = self.rule("12").mandatory_group
        self.assertEqual(list(group.rules.all()), [self.rule("12")])
        self.assertEqual(group.name, "ข้อ 12 มีใบรับรอง")
        self.assertEqual(DistributorRuleGroup.objects.count(), groups_before + 1)

    def test_create_or_joins_existing_group(self):
        self.save_rule(kind="main", code="12", name="ISO 14001", requirement="or", alternatives=[self.rule("8").pk])
        group = self.rule("8").mandatory_group
        self.assertEqual(sorted(group.rules.values_list("code", flat=True)), ["12", "8", "9"])
        self.assertEqual(group.name, "ข้อ 8 หรือ ข้อ 9 หรือ ข้อ 12")

    # ----- แก้ไขข้อ -----

    def test_edit_shows_current_answers(self):
        response = self.client.get(reverse("distributorRuleEdit", args=[self.rule("9").pk]))
        form = response.context["form"]
        self.assertEqual(form["requirement"].value(), "or")
        self.assertEqual(form["alternatives"].value(), [self.rule("8").pk])
        self.assertTrue(form.has_children)
        self.assertContains(response, "ข้อย่อยต้องผ่านแค่ไหน")

    def test_or_to_yes_splits_group(self):
        self.save_rule(self.rule("9"), kind="main", code="9", name="ISO", requirement="yes", children_mode="any")
        nine, eight = self.rule("9"), self.rule("8")
        self.assertNotEqual(nine.mandatory_group, eight.mandatory_group)
        self.assertEqual(self.requirement("8"), "บังคับ")
        self.assertEqual(self.requirement("9"), "บังคับ")
        self.assertEqual(nine.children_mode, "any")

    def test_unchecked_alternative_stays_required_alone(self):
        # ข้อ 9 เปลี่ยนจาก "8 หรือ 9" เป็น "9 หรือ 10" -> ข้อ 8 ยังบังคับ แต่อยู่ลำพัง
        self.save_rule(self.rule("9"), kind="main", code="9", name="ISO", requirement="or", alternatives=[self.rule("10").pk])
        self.assertEqual(self.requirement("9"), "บังคับ (ใช้ ข้อ 10 แทนได้)")
        self.assertEqual(self.requirement("10"), "บังคับ (ใช้ ข้อ 9 แทนได้)")
        self.assertEqual(self.requirement("8"), "บังคับ")

    def test_not_required_leaves_partner_required(self):
        self.save_rule(self.rule("9"), kind="main", code="9", name="ISO", requirement="no")
        self.assertEqual(self.requirement("9"), "")
        self.assertEqual(self.requirement("8"), "บังคับ")
        self.assertFalse(DistributorRuleGroup.objects.filter(rules__isnull=True).exists())

    def test_main_to_child_clears_requirement(self):
        three = self.rule("3")
        self.save_rule(three, kind="child", parent=self.rule("1").pk, code="1.1", name=three.name)
        three.refresh_from_db()
        self.assertEqual((three.parent, three.mandatory_group), (self.rule("1"), None))

    def test_validation(self):
        nine = self.rule("9")
        cases = [
            (dict(kind="child", parent=self.rule("1").pk, code="9", name="x"), "kind"),  # มีข้อย่อยแล้ว
            (dict(kind="main", code="9", name="x", requirement="or"), "alternatives"),  # ไม่ได้เลือกข้อแทน
            (dict(kind="main", code="8", name="x", requirement="no"), "code"),  # เลขข้อซ้ำ
        ]
        for data, field in cases:
            response = self.save_rule(nine, **data)
            self.assertEqual(response.status_code, 200, data)
            self.assertIn(field, response.context["form"].errors, data)
        response = self.save_rule(kind="child", code="20", name="x")
        self.assertIn("parent", response.context["form"].errors)
        # ข้อย่อยเป็นข้อหลักของข้ออื่นไม่ได้ (ซ้อนได้ชั้นเดียว)
        self.assertNotIn(self.rule("9.1"), response.context["form"].fields["parent"].queryset)

    # ----- ปิด / ย้าย / ลบ -----

    def test_toggle_active(self):
        self.post("distributorRuleToggle", self.rule("11").pk)
        self.assertFalse(self.rule("11").is_active)
        self.post("distributorRuleToggle", self.rule("11").pk)
        self.assertTrue(self.rule("11").is_active)

    def test_children_follow_inactive_parent(self):
        self.post("distributorRuleToggle", self.rule("9").pk)
        c = DistributorCandidate.objects.create(place_source="osm", place_id="node/1", name="x")
        codes = [row["rule"].code for row in c.evaluate()["rows"]]
        self.assertNotIn("9.1", codes)
        self.assertNotIn("9.1", [r.code for r in c.evaluate()["missing"]])
        self.assertContains(self.client.get(reverse("distributorRuleList")), "ปิดตามข้อ 9")

    def test_child_in_group_is_cleaned_on_save(self):
        # ข้อมูลเก่าที่ตั้งผ่าน admin: ข้อย่อย 9.1 อยู่ในกลุ่มของข้อ 2
        DistributorRule.objects.filter(code="9.1").update(mandatory_group=self.rule("2").mandatory_group)
        self.save_rule(self.rule("3"), kind="main", code="3", name="ประวัติ", requirement="no")
        self.assertIsNone(self.rule("9.1").mandatory_group)
        self.assertEqual(self.requirement("2"), "บังคับ")

    def test_move_up_and_down_within_siblings(self):
        top = lambda: list(DistributorRule.objects.filter(parent__isnull=True).order_by("order").values_list("code", flat=True))
        self.post("distributorRuleMove", self.rule("2").pk, "up")
        self.assertEqual(top()[:3], ["2", "1", "3"])
        self.post("distributorRuleMove", self.rule("2").pk, "down")
        self.assertEqual(top()[:3], ["1", "2", "3"])
        # ข้อย่อยย้ายเฉพาะในข้อหลักเดียวกัน
        self.post("distributorRuleMove", self.rule("9.2").pk, "up")
        kids = list(self.rule("9").children.order_by("order").values_list("code", flat=True))
        self.assertEqual(kids, ["9.2", "9.1"])
        # ข้อแรกกด "ขึ้น" ไม่มีผล / ทิศอื่น 404
        self.post("distributorRuleMove", self.rule("1").pk, "up")
        self.assertEqual(top()[0], "1")
        self.assertEqual(self.post("distributorRuleMove", self.rule("1").pk, "left").status_code, 404)

    def test_delete_only_when_unused(self):
        c = DistributorCandidate.objects.create(place_source="osm", place_id="node/1", name="x")
        DistributorForm.objects.create(candidate=c, question=self.rule("3"), ans="pass")
        self.post("distributorRuleDelete", self.rule("3").pk)
        self.post("distributorRuleDelete", self.rule("9").pk)
        self.assertEqual(DistributorRule.objects.filter(code__in=["3", "9"]).count(), 2)

        self.post("distributorRuleDelete", self.rule("8").pk)
        self.assertFalse(DistributorRule.objects.filter(code="8").exists())
        # ข้อ 8 หายจากกลุ่ม -> ข้อ 9 เหลือบังคับลำพัง
        self.assertEqual(self.requirement("9"), "บังคับ")

    def test_approve_page_links_to_rules(self):
        response = self.client.get(reverse("distributorApproveList"))
        self.assertContains(response, reverse("distributorRuleList"))
