from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class SboutURLTests(TestCase):
    def setUp(self) -> None:
        self.guest_client: Client = Client()

    def test_about_urls_exist(self) -> None:
        """Pages are available to any user."""
        url_names: list = [
            '/about/author/',
            '/about/tech/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response: HttpResponse = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_correct_template(self) -> None:
        """The URL uses the appropriate template."""
        url_templates: dict = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response: HttpResponse = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_about_uses_correct_template(self) -> None:
        """Namespase:name about correct templage."""
        templates_page_names: dict = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response: HttpResponse = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
