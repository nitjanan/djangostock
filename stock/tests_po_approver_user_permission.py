from django.contrib.auth.models import Group, User
from django.test import TestCase

from stock.views import can_edit_approver_user_po


class CanEditApproverUserPOTestCase(TestCase):
    """สิทธิเลือกผู้อนุมัติใบสั่งซื้อ: แก้ได้เฉพาะใบที่ออกจาก PR ส่วนใบจาก CP ปิดตาย"""

    def setUp(self):
        self.purchasing_group, _ = Group.objects.get_or_create(name='จัดซื้อ')
        self.edit_approver_group, _ = Group.objects.get_or_create(name='แก้ไขผู้อนุมัติใบสั่งซื้อ')

    def make_user(self, username, groups=()):
        user = User.objects.create_user(username=username, password='password')
        for group in groups:
            user.groups.add(group)
        return user

    def test_purchasing_can_edit_when_po_from_pr(self):
        user = self.make_user('purchasing_pr', [self.purchasing_group])
        self.assertTrue(can_edit_approver_user_po(user, False))

    def test_purchasing_cannot_edit_when_po_from_cp(self):
        user = self.make_user('purchasing_cp', [self.purchasing_group])
        self.assertFalse(can_edit_approver_user_po(user, True))

    def test_edit_approver_group_can_edit_only_po_from_pr(self):
        user = self.make_user('edit_approver', [self.edit_approver_group])
        self.assertTrue(can_edit_approver_user_po(user, False))
        #ใบที่ออกจาก CP ปิดตายทุกคน เพราะ approver_user ถูกดึงมาจากใบ CP อัตโนมัติ
        self.assertFalse(can_edit_approver_user_po(user, True))

    def test_user_without_group_cannot_edit(self):
        user = self.make_user('plain_user')
        self.assertFalse(can_edit_approver_user_po(user, False))
        self.assertFalse(can_edit_approver_user_po(user, True))
