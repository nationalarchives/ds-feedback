from datetime import timedelta

from django.utils import timezone

from rest_framework.test import APITestCase

from app.api.acl import (
    can_access_any_project_with_role,
    can_access_project_with_role,
    get_accessible_projects_with_role,
)
from app.api.factories import APIAccessLifespanFactory, TokenFactory
from app.api.types import APIRole
from app.projects.factories import ProjectFactory
from app.users.factories import StaffUserFactory, UserFactory
from app.utils.testing import ResetFactorySequencesMixin


class TestAcl(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user_1 = UserFactory()
        cls.user_2 = UserFactory()

        cls.admin_user = StaffUserFactory(is_superuser=True)
        cls.admin_token = TokenFactory(user=cls.admin_user)

        cls.project_1 = ProjectFactory.create(created_by=cls.admin_user)
        cls.project_2 = ProjectFactory.create(created_by=cls.admin_user)
        cls.project_3 = ProjectFactory.create(created_by=cls.admin_user)
        cls.project_4 = ProjectFactory.create(created_by=cls.admin_user)
        cls.project_5 = ProjectFactory.create(created_by=cls.admin_user)

        APIAccessLifespanFactory(
            project=cls.project_1,
            grantee=cls.user_1,
            role=APIRole.EXPLORE_RESPONSES,
            created_by=cls.admin_user,
        )

        APIAccessLifespanFactory(
            project=cls.project_2,
            grantee=cls.user_1,
            role=APIRole.EXPLORE_RESPONSES,
            created_by=cls.admin_user,
        )
        APIAccessLifespanFactory(
            project=cls.project_2,
            grantee=cls.user_1,
            role=APIRole.SUBMIT_RESPONSES,
            created_by=cls.admin_user,
        )

        APIAccessLifespanFactory(
            project=cls.project_3,
            grantee=cls.user_1,
            role=APIRole.EXPLORE_RESPONSES,
            created_by=cls.admin_user,
            expires_at=timezone.now() - timedelta(hours=1),
        )

        APIAccessLifespanFactory(
            project=cls.project_3,
            grantee=cls.user_2,
            role=APIRole.SUBMIT_RESPONSES,
            created_by=cls.admin_user,
            expires_at=timezone.now() - timedelta(hours=1),
        )

        APIAccessLifespanFactory(
            project=cls.project_5,
            grantee=cls.user_1,
            role=APIRole.SUBMIT_RESPONSES,
            created_by=cls.admin_user,
        )

    def test_can_access_project_with_correct_role(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_1,
            allowed_roles=[APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, True)

    def test_can_access_project_including_correct_role(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_1,
            allowed_roles=[APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, True)

    def test_can_access_project_fails_with_incorrect_role(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_1,
            allowed_roles=[APIRole.SUBMIT_RESPONSES],
        )

        self.assertEqual(result, False)

    def test_can_access_project_with_correct_role_of_multiple(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_2,
            allowed_roles=[APIRole.SUBMIT_RESPONSES],
        )

        self.assertEqual(result, True)

    def test_can_access_project_including_with_multiple_correct_roles(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_2,
            allowed_roles=[APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, True)

    def test_can_access_project_fails_with_expired_access(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_3,
            allowed_roles=[APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, False)

    def test_can_access_project_fails_no_access(self):
        result = can_access_project_with_role(
            user=self.user_1,
            project=self.project_4,
            allowed_roles=[APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, False)

    def can_access_any_project_with_role(self):
        result = can_access_any_project_with_role(
            user=self.user_1,
            allowed_roles=[APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, True)

    def can_access_any_project_with_multiple_roles(self):
        result = can_access_any_project_with_role(
            user=self.user_1,
            allowed_roles=[APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, True)

    def can_access_any_project_fails(self):
        result = can_access_any_project_with_role(
            user=self.user_2,
            allowed_roles=[APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(result, False)

    def test_get_accessible_projects_with_role(self):
        result = get_accessible_projects_with_role(
            user=self.user_1,
            allowed_roles=[APIRole.EXPLORE_RESPONSES],
        )

        self.assertEqual(list(result), [self.project_1, self.project_2])

    def test_get_accessible_projects_with_multiple_roles(self):
        result = get_accessible_projects_with_role(
            user=self.user_1,
            allowed_roles=[APIRole.EXPLORE_RESPONSES, APIRole.SUBMIT_RESPONSES],
        )

        self.assertEqual(
            list(result), [self.project_1, self.project_2, self.project_5]
        )

    def test_get_accessible_projects_with_role_is_empty(self):
        result = get_accessible_projects_with_role(
            user=self.user_2,
            allowed_roles=[APIRole.SUBMIT_RESPONSES],
        )

        self.assertEqual(list(result), [])
