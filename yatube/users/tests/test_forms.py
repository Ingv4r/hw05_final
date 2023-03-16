from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

User: AbstractBaseUser = get_user_model()


class PostsCreateFormTests(TestCase):
    def setUp(self) -> None:
        self.guest_client: Client = Client()
        self.username = 'User2'
        self.password = 'Pass123R'

    def test_user_create(self) -> None:
        """When filling out the form, a new user is created."""
        users_before_create: int = User.objects.all().count()
        form_data: dict = {
            'username': self.username,
            'password1': self.password,
            'password2': self.password,
        }
        response: HttpResponse = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.all().count(), users_before_create + 1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            User.objects.filter(username=form_data['username']).exists()
        )
