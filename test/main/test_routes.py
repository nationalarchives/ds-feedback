from django.test import TestCase


class MainTestCase(TestCase):
    def test_healthcheck_live(self):
        rv = self.client.get("/healthcheck/live/")
        self.assertContains(rv, "ok", status_code=200)

    def test_trailing_slash_redirects(self):
        rv = self.client.get("/healthcheck/live")
        self.assertEqual(rv.status_code, 301)
        self.assertEqual(rv.url, "/healthcheck/live/")

    def test_cookies(self):
        rv = self.client.get("/cookies/")
        self.assertContains(
            rv, '<h1 class="tna-heading-xl">Cookies</h1>', status_code=200
        )
