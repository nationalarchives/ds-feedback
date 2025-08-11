from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from app.users.factories import StaffUserFactory
from app.utils.testing import ResetFactorySequencesMixin, reverse_with_query


class TestIndexView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory()

    def test_get_index_not_authorised(self):
        response = self.client.get(reverse("main:index"))
        login_url = reverse_with_query("editor_auth:login", {"next": "/"})
        self.assertRedirects(response, login_url)

    def test_get_index_authorised(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestAdminIndexView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory()

    def test_get_login(self):
        response = self.client.get(reverse("editor_auth:login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_index_not_authorised(self):
        response = self.client.get(reverse("admin:index"))
        login_url = reverse_with_query(
            "admin:login", {"next": reverse("admin:index")}
        )
        self.assertRedirects(response, login_url)

    def test_get_index_authorised(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
