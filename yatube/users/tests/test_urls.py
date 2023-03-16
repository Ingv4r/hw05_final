from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self) -> None:
        self.guest_client: Client = Client()
        self.authorized_client: Client = Client()
        self.user: AbstractBaseUser = User.objects.create_user(username='auth')
        self.authorized_client.force_login(self.user)

    def test_users_urls_exist_guest(self) -> None:
        """Pages are available to any user."""
        url_names: list = [
            '/auth/logout/',
            '/auth/login/',
            '/auth/signup/',
            '/auth/reset/done/',
            '/auth/password_reset/done/',
            '/auth/password_reset/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response: HttpResponse = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_urls_exist_auth_user(self) -> None:
        """Pages are available to an authorized user."""
        url_names: list = [
            '/auth/password_change/done/',
            '/auth/password_change/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response: HttpResponse = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_redirects_guest(self) -> None:
        """Pages redirect the anonymous user to the login page."""
        url_from_to: dict = {
            '/auth/password_change/done/': (
                '/auth/login/?next=/auth/password_change/done/'
            ),
            '/auth/password_change/': (
                '/auth/login/?next=/auth/password_change/'
            ),
        }
        for redirect_from, redirect_to in url_from_to.items():
            with self.subTest(redirect_from=redirect_from):
                response: HttpResponse = self.guest_client.get(
                    redirect_from, follow=True
                )
                self.assertRedirects(response, redirect_to)

    def test_urls_correct_template(self) -> None:
        """The URL uses the appropriate template."""
        template_url_names: dict = {
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_change/': 'users/password_change.html',
            '/auth/logout/': 'users/logged_out.html',
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response: HttpResponse = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
