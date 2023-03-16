import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user: AbstractBaseUser = User.objects.create_user(username='Igor')
        cls.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post: Post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=PostsViewsTests.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client: Client = Client()
        self.authorized_client: Client = Client()
        self.authorized_client.force_login(PostsViewsTests.user)
        cache.clear()

    def test_pages_uses_correct_template(self) -> None:
        """Namespase:name posts correct templage"""
        templates_page_names: dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user.username}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.pk}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:update_post',
                kwargs={'post_id': f'{self.post.pk}'}
            ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response: HttpResponse = self.authorized_client.get(
                    reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_correct_context(self) -> None:
        """Create and update posts template
        is formed with the correct context.
        """
        response_create: HttpResponse = self.authorized_client.get(
            reverse('posts:post_create')
        )
        response_update: HttpResponse = self.authorized_client.get(
            reverse(
                'posts:update_post',
                kwargs={'post_id': f'{self.post.pk}'}
            )
        )
        form_fields: dict = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_create.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
                form_field = response_update.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_detail(self) -> None:
        """Post_detail template is formed with the correct context."""
        posts_number: int = 1
        response: HttpResponse = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['title'], self.post.text)
        self.assertEqual(response.context['posts_number'], posts_number)
        self.assertEqual(response.context['image'], self.post.image)

    def test_post_image_context(self) -> None:
        """Urls with image are formed with the correct context."""
        reverse_names: list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        responses: list = [
            self.guest_client.get(i) for i in reverse_names
        ]
        for response in responses:
            only_post: Post = response.context['page_obj'][0]
            self.assertEqual(only_post.image, self.post.image)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PaginatorViewsTest(TestCase):
    TEST_POSTS_NUMBER: int = 13
    FIRST_PAGE_POSTS: int = 10
    SECOND_PAGE_POSTS: int = 3

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user: AbstractBaseUser = User.objects.create_user(username='Igor')
        cls.group: Group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_1',
            description='Тестовое описание 1',
        )
        cls.unused_group: Group = Group.objects.create(
            title='Не испольуемая группа',
            slug='unused',
            description='Опаисание'
        )
        cls.posts_list: list[Post] = []
        for post_number in range(cls.TEST_POSTS_NUMBER):
            cls.posts_list.append(
                Post.objects.create(
                    author=cls.user,
                    text='Это пост номер',
                    group=cls.group,
                )
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client: Client = Client()
        self.urls_paginator_names: list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        cache.clear()

    def test_task_list_page_show_correct_context(self) -> None:
        """Paginator templates are formed with the correct context."""
        responses: list[HttpResponse] = [
            self.guest_client.get(i) for i in self.urls_paginator_names
        ]
        for response in responses:
            with self.subTest(response=response):
                first_object: Post = response.context['page_obj'][0]
                post_author_0: AbstractBaseUser = first_object.author
                post_text_0: str = first_object.text
                post_group_0: None = first_object.group
                self.assertEqual(post_author_0, self.user)
                self.assertEqual(post_text_0, self.posts_list[-1].text)
                self.assertEqual(post_group_0, self.group)

    def test_first_page_contains_ten_posts(self) -> None:
        """Paginator first page shows the required number of posts."""
        for reverse_name in self.urls_paginator_names:
            with self.subTest(reverse_name=reverse_name):
                response: HttpResponse = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.FIRST_PAGE_POSTS
                )

    def test_second_page_contains_three_posts(self) -> None:
        """Paginator second page shows the required number of posts."""
        for reverse_name in self.urls_paginator_names:
            with self.subTest(reverse_name=reverse_name):
                response: HttpResponse = self.guest_client.get(
                    reverse_name + '?page=2'
                )
                self.assertEqual(
                    len(response.context['page_obj']), self.SECOND_PAGE_POSTS
                )

    def test_unused_group(self) -> None:
        """There are no posts with wrong group."""
        posts_number = 0
        response: HttpResponse = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.unused_group.slug}
        ))
        self.assertEqual(len(response.context['page_obj']), posts_number)
