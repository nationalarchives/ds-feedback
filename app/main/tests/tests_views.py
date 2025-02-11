from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode


class TestIndexView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestIndexView, cls).setUpClass()
        cls.admin_user = User.objects.create_user(
            username="test", password="password", is_staff=True
        )

    def test_get_index_not_authorised(self):
        response = self.client.get(reverse("main:index"))
        login_url = reverse("admin:login") + '?' + urlencode({"next": "/"})
        self.assertRedirects(response, login_url, HTTPStatus.FOUND)

    def test_get_index_authorised(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestAdminIndexView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestAdminIndexView, cls).setUpClass()
        cls.admin_user = User.objects.create_user(
            username="test", password="password", is_staff=True
        )

    def test_get_login(self):
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_index_not_authorised(self):
        response = self.client.get(reverse("admin:index"))
        login_url = reverse("admin:login") + '?' + urlencode({"next": reverse("admin:index")})
        self.assertRedirects(response, login_url, HTTPStatus.FOUND)

    def test_get_index_authorised(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
