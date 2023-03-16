from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user: AbstractBaseUser = User.objects.create_user(username='Boris')
        cls.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post: Post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment: Comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий',
        )

    def test_models_have_correct_object_names(self) -> None:
        """Сheck that __str__ is working correctly for the models."""
        group: Group = self.group
        post: Post = self.post
        comment: Comment = self.comment
        expected_strings: dict = {
            str(group): group.title,
            str(post): post.text[:15],
            str(comment): comment.text[:15]
        }
        for value, expected in expected_strings.items():
            with self.subTest(value=value):
                self.assertEqual(
                    value, expected
                )

    def test_verbose_name(self) -> None:
        """Verbose_name in the fields matches expected."""
        post: Post = PostModelTest.post
        field_verboses: dict = {
            'text': 'Текст записи',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self) -> None:
        """The help_text in the fields matches expected."""
        post: Post = PostModelTest.post
        field_help_texts: dict = {
            'text': 'Введите текст записи',
            'group': 'Группа, к которой будет относиться запись',
            'image': 'Можете загрузить изображение'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )
