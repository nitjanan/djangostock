"""
Regression tests for adding the optional ``user`` ForeignKey to
``PositionBasePermission`` (migration 0146_positionbasepermission_user).

Goal: prove the new field is a purely additive, optional relationship and that
the existing rule  Position -> PositionBasePermission -> BasePermission  is
unchanged, for both ``user = NULL`` and ``user = <User>``.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib import admin

from stock.models import (
    Position, BasePermission, PositionBasePermission, UserProfile,
    BaseBranchCompany,
)


class PositionBasePermissionUserFieldTestCase(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="PBP-USER Position A")
        self.position_b = Position.objects.create(name="PBP-USER Position B")
        self.perm = BasePermission.objects.create(
            name="PBP-USER perm", codename="PBPUSER1", codename_th="PBPUSER1-th",
        )
        self.branch = BaseBranchCompany.objects.create(
            id="pbpu1", code="PBPU1", name="PBP-USER Branch",
        )
        self.user = User.objects.create_user(username="pbp_user_1", password="x")

    # ---- helpers -----------------------------------------------------------
    def _make(self, user=None, position=None):
        pbp = PositionBasePermission.objects.create(
            position=position or self.position, user=user,
        )
        pbp.base_permission.add(self.perm)
        pbp.branch_company.add(self.branch)
        return pbp

    # ---- matrix: CRUD with / without user --------------------------------
    def test_create_without_user(self):
        pbp = self._make(user=None)
        pbp.refresh_from_db()
        self.assertIsNone(pbp.user)
        self.assertIsNone(pbp.user_id)
        # accessing the FK must not raise RelatedObjectDoesNotExist
        self.assertEqual(pbp.user, None)

    def test_create_with_user(self):
        pbp = self._make(user=self.user)
        pbp.refresh_from_db()
        self.assertEqual(pbp.user, self.user)
        self.assertEqual(pbp.user_id, self.user.id)

    def test_read_existing_null_user(self):
        pk = self._make(user=None).pk
        fetched = PositionBasePermission.objects.get(pk=pk)
        self.assertIsNone(fetched.user)
        self.assertEqual(str(fetched), self.position.name)  # __str__ unchanged

    def test_read_with_user(self):
        pk = self._make(user=self.user).pk
        fetched = PositionBasePermission.objects.select_related("user").get(pk=pk)
        self.assertEqual(fetched.user.username, "pbp_user_1")

    def test_update_without_changing_user(self):
        pbp = self._make(user=self.user)
        pbp.branch_company.clear()
        pbp.save()
        pbp.refresh_from_db()
        self.assertEqual(pbp.user, self.user)

    def test_update_assign_user(self):
        pbp = self._make(user=None)
        pbp.user = self.user
        pbp.save()
        pbp.refresh_from_db()
        self.assertEqual(pbp.user, self.user)

    def test_update_remove_user(self):
        pbp = self._make(user=self.user)
        pbp.user = None
        pbp.save()
        pbp.refresh_from_db()
        self.assertIsNone(pbp.user)

    def test_delete_positionbasepermission_keeps_user(self):
        pbp = self._make(user=self.user)
        pbp.delete()
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_user_cascades_only_its_rows(self):
        linked = self._make(user=self.user)
        unlinked = self._make(user=None, position=self.position_b)
        self.user.delete()
        self.assertFalse(PositionBasePermission.objects.filter(pk=linked.pk).exists())
        self.assertTrue(PositionBasePermission.objects.filter(pk=unlinked.pk).exists())

    def test_reverse_accessor(self):
        pbp = self._make(user=self.user)
        self.assertEqual(list(self.user.positionbasepermission_set.all()), [pbp])

    # ---- existing business logic must be unchanged ----------------------
    def test_position_based_permission_lookup_unchanged(self):
        """
        The app resolves permissions with queries shaped like
        PositionBasePermission.objects.filter(position_id=..., base_permission__codename=...)
        Result must be identical whether the row has a user or not.
        """
        self._make(user=None)                      # row for self.position
        qs_null = PositionBasePermission.objects.filter(
            position_id=self.position.id, base_permission__codename="PBPUSER1",
        )
        self.assertEqual(qs_null.count(), 1)

        # same row, now with a user attached -> lookup still finds it by position
        PositionBasePermission.objects.filter(position_id=self.position.id).update(
            user=self.user,
        )
        qs_with_user = PositionBasePermission.objects.filter(
            position_id=self.position.id, base_permission__codename="PBPUSER1",
        )
        self.assertEqual(qs_with_user.count(), 1)
        self.assertEqual(list(qs_null.values_list("id", flat=True)),
                         list(qs_with_user.values_list("id", flat=True)))

    def test_full_permission_chain_user_profile_position(self):
        """User -> UserProfile -> Position -> PositionBasePermission -> BasePermission"""
        profile = UserProfile.objects.create(user=self.user, position=self.position)
        profile.branch_company.add(self.branch)
        self._make(user=None)  # permission granted to the POSITION, not the user

        up = UserProfile.objects.get(user=self.user)
        granted = PositionBasePermission.objects.filter(
            position_id=up.position_id,
        ).values_list("base_permission__codename", flat=True)
        self.assertIn("PBPUSER1", list(granted))

    def test_values_with_explicit_fields_not_affected(self):
        self._make(user=self.user)
        row = PositionBasePermission.objects.filter(
            position_id=self.position.id,
        ).values("branch_company__code", "base_permission").first()
        self.assertEqual(set(row.keys()), {"branch_company__code", "base_permission"})

    # ---- focused: valid Position + user = NULL --------------------------
    def test_null_user_multiple_users_same_position(self):
        """
        One PositionBasePermission (Position A, user=NULL). Several users all sit
        on Position A via UserProfile. Every user must resolve the permission
        through the Position - the NULL user must not gate anyone out.
        """
        self._make(user=None)  # single grant to the POSITION
        users = []
        for i in range(3):
            u = User.objects.create_user(username="multi_pos_%d" % i, password="x")
            p = UserProfile.objects.create(user=u, position=self.position)
            p.branch_company.add(self.branch)
            users.append(u)

        for u in users:
            up = UserProfile.objects.get(user=u)
            codenames = list(
                PositionBasePermission.objects
                .filter(position_id=up.position_id)
                .values_list("base_permission__codename", flat=True)
            )
            self.assertEqual(codenames, ["PBPUSER1"], u.username)

    def test_null_user_query_method_sweep(self):
        """Adding user=NULL must not drop the row from any common query form."""
        pbp = self._make(user=None)
        pos_id = self.position.id

        self.assertTrue(
            PositionBasePermission.objects.filter(position_id=pos_id).exists())
        self.assertEqual(
            PositionBasePermission.objects.filter(position=self.position).first(), pbp)
        self.assertIn(
            pbp,
            PositionBasePermission.objects.filter(position_id=pos_id, user__isnull=True))
        # excluding rows that HAVE a user must keep this NULL row
        self.assertIn(
            pbp,
            PositionBasePermission.objects.exclude(user__isnull=False))
        # select_related('user') on a NULL FK is safe and yields None
        got = (PositionBasePermission.objects
               .select_related("user", "position")
               .get(pk=pbp.pk))
        self.assertIsNone(got.user)
        self.assertEqual(got.position, self.position)
        # prefetch of the M2M still works with a NULL user row
        got2 = (PositionBasePermission.objects
                .prefetch_related("base_permission", "branch_company")
                .get(pk=pbp.pk))
        self.assertEqual([p.codename for p in got2.base_permission.all()], ["PBPUSER1"])

    def test_edit_null_user_row_via_orm_keeps_null(self):
        pbp = self._make(user=None)
        pbp.position = self.position_b          # change only the Position
        pbp.save()
        pbp.refresh_from_db()
        self.assertEqual(pbp.position, self.position_b)
        self.assertIsNone(pbp.user)
        # permission still resolvable through the (new) Position
        self.assertTrue(
            PositionBasePermission.objects
            .filter(position_id=self.position_b.id, base_permission__codename="PBPUSER1")
            .exists())

    def test_multiple_rows_same_position(self):
        a = self._make(user=None)
        b = self._make(user=self.user)
        self.assertEqual(
            PositionBasePermission.objects.filter(position_id=self.position.id).count(),
            2,
        )
        self.assertCountEqual(
            PositionBasePermission.objects.filter(position_id=self.position.id)
            .values_list("id", flat=True),
            [a.id, b.id],
        )


class PositionBasePermissionAdminTestCase(TestCase):
    def setUp(self):
        from stock.forms import PositionBasePermissionAdminForm
        self.Form = PositionBasePermissionAdminForm
        self.position = Position.objects.create(name="ADM Position")
        self.other_position = Position.objects.create(name="ADM Other Position")
        self.perm = BasePermission.objects.create(
            name="ADM perm", codename="ADMPERM1", codename_th="ADMPERM1-th",
        )
        self.branch = BaseBranchCompany.objects.create(
            id="admb1", code="ADMB1", name="ADM Branch",
        )
        self.user = User.objects.create_user(username="adm_user", password="x")

    def _data(self, **over):
        data = {
            "user": self.user.id,
            "position": self.position.id,
            "base_permission": [self.perm.id],
            "branch_company": [self.branch.id],
        }
        data.update(over)
        return data

    def test_admin_registered_with_custom_classes(self):
        self.assertIn(PositionBasePermission, admin.site._registry)
        self.assertIn(User, admin.site._registry)

    def test_form_requires_user(self):
        form = self.Form(data=self._data(user=""))
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_form_invalid_when_user_has_no_profile(self):
        form = self.Form(data=self._data())
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_form_invalid_when_profile_has_no_position(self):
        UserProfile.objects.create(user=self.user, position=None)
        form = self.Form(data=self._data())
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_model_full_clean_allows_null_user(self):
        """Model-level validation (blank=True) must accept user=NULL."""
        from django.core.exceptions import ValidationError
        obj = PositionBasePermission(position=self.position, user=None)
        try:
            obj.full_clean(exclude=["base_permission", "branch_company"])
        except ValidationError as exc:
            self.assertNotIn("user", exc.message_dict)

    def test_admin_form_requires_user_by_design(self):
        """
        The NEW admin form (PositionBasePermissionAdminForm) intentionally makes
        `user` required so it can auto-derive Position from UserProfile. This is a
        deliberate admin-form constraint and does NOT propagate to the model,
        the ORM, or Position-based permission resolution.
        """
        UserProfile.objects.create(user=self.user, position=self.position)
        form = self.Form(data=self._data(user=""))
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)
        # model still allows it:
        self.assertTrue(PositionBasePermission._meta.get_field("user").null)
        self.assertTrue(PositionBasePermission._meta.get_field("user").blank)

    def test_form_valid_forces_position_from_profile(self):
        UserProfile.objects.create(user=self.user, position=self.position)
        # submit a DIFFERENT position -> clean() must override it with the profile's
        form = self.Form(data=self._data(position=self.other_position.id))
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save()
        self.assertEqual(obj.position, self.position)
        self.assertEqual(obj.user, self.user)
