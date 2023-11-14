import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user: AbstractBaseUser = User.objects.create_user(username='Igor')
        cls.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post: Post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=PostsCreateFormTests.group
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post_form = PostForm()
        cls.comment_form = CommentForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.guest_client: Client = Client()
        self.authorized_client: Client = Client()
        self.authorized_client.force_login(PostsCreateFormTests.user)

    def test_create_post(self) -> None:
        """A valid form creates a Post entry."""
        posts_count: int = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data: dict = {
            'text': 'Тестовый пост 2',
            'group': self.group.pk,
            'image': uploaded,
        }
        response: HttpResponse = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image='posts/small.gif',
                pk=posts_count + 1
            ).exists()
        )

    def test_update_post(self) -> None:
        """Post change with the post_id in the database."""
        posts_count: int = Post.objects.count()
        form_data: dict = {
            'text': 'Изменение текста поста 1',
            'group': self.group.pk,
        }
        response: HttpResponse = self.authorized_client.post(
            reverse(
                'posts:update_post',
                kwargs={'post_id': f'{self.post.pk}'},
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.pk}'}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                pk=self.post.pk
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_add_comment(self) -> None:
        """After submission, the comment appears on the post page."""
        comments_count: int = Comment.objects.select_related(
            'author'
        ).count()
        form_data: dict = {'text': 'Комментарий'}
        response: HttpResponse = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.post.pk}'},
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.pk}'}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists()
        )

    def test_title_label(self) -> None:
        """Testing label content in models."""
        text_label: str = self.post_form.fields['text'].label
        group_label: str = self.post_form.fields['group'].label
        comment_label: str = self.comment_form.fields['text'].label
        self.assertEqual(text_label, 'Текст записи')
        self.assertEqual(group_label, 'Группа')
        self.assertEqual(comment_label, 'Комментарий:')
