from http import HTTPStatus

from django.http import HttpResponse
from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self) -> None:
        """Unexisting page not found and use custom template."""
        response: HttpResponse = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
