from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersViewsTests(TestCase):
    def setUp(self) -> None:
        self.user: AbstractBaseUser = User.objects.create_user(
            username='Boris'
        )
        self.guest_client: Client = Client()
        self.authorized_client: Client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_uses_correct_template(self) -> None:
        """Namespase:name users correct templage."""
        templates_page_names: dict = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_change'): 'users/password_change.html',
            reverse(
                'users:password_change_done'
            ): 'users/password_change_done.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'
            ): 'users/password_reset_done.html',
            reverse(
                'users:password_reset_complete'
            ): 'users/password_reset_complete.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response: HttpResponse = self.authorized_client.get(
                    reverse_name)
                self.assertTemplateUsed(response, template)

    def test_users_signup_correct_context(self) -> None:
        """User signup form using correct context."""
        response: HttpResponse = self.guest_client.get(
            reverse('users:signup')
        )
        form_fields: dict = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
