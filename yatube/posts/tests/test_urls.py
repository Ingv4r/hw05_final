from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.test import Client, TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user: AbstractBaseUser = User.objects.create_user(username='Igor')
        cls.another_user: AbstractBaseUser = User.objects.create_user(
            username='Mumble'
        )
        cls.post: Post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.another_user_post: Post = Post.objects.create(
            author=cls.another_user,
            text='Делай ноги!',
        )
        Follow.objects.create(user=cls.user, author=cls.another_user)
        cls.url_names: dict = {
            'index': '/',
            'group_posts': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.user.username}/',
            'post': f'/posts/{cls.post.pk}/',
            'post_edit': f'/posts/{cls.post.pk}/edit/',
            'create': '/create/',
            'unfollow': f'/profile/{cls.another_user.username}/unfollow/',
            'follow': f'/profile/{cls.another_user.username}/follow/'
        }

    def setUp(self) -> None:
        self.guest_client: Client = Client()
        self.authorized_client: Client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        self.follows_count = Follow.objects.filter(user=self.user.id).count()
        cache.clear()

    def test_posts_urls_exist_guest(self) -> None:
        """Pages are available to any user."""
        urls: list[str] = [
            self.url_names['index'],
            self.url_names['group_posts'],
            self.url_names['profile'],
            self.url_names['post']
        ]
        for url in urls:
            with self.subTest(url=url):
                response: HttpResponse = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_custom_404_page(self) -> None:
        """Unexisting page not found and use custom template."""
        response: HttpResponse = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_posts_urls_exist_authorized(self) -> None:
        """Pages are available to an authorized user."""
        urls: list[str] = [
            self.url_names['create'],
            self.url_names['post_edit'],
        ]
        for url in urls:
            with self.subTest(url=url):
                response: HttpResponse = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_urls_edit_not_author(self) -> None:
        """Edit a post only by the author of the post"""
        response: HttpResponse = self.authorized_client.get(
            f'/posts/{self.another_user_post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/posts/{self.another_user_post.pk}/'
        )

    def test_posts_url_redirects_guest(self) -> None:
        """Pages redirect the anonymous user to the login page."""
        next = '/auth/login/?next={}'
        redirect_from_to_url: dict = {
            self.url_names['post_edit']: (
                next.format(self.url_names['post_edit'])
            ),
            self.url_names['create']: (
                next.format(self.url_names['create'])
            ),
        }
        for redirect_from, redirect_to in redirect_from_to_url.items():
            with self.subTest(redirect_from=redirect_from):
                response: HttpResponse = self.guest_client.get(
                    redirect_from, follow=True
                )
                self.assertRedirects(response, redirect_to)

    def test_urls_correct_template(self) -> None:
        """The URL uses the appropriate template."""
        template_url_names: dict[str, str] = {
            self.url_names['index']: 'posts/index.html',
            self.url_names['group_posts']: 'posts/group_list.html',
            self.url_names['profile']: 'posts/profile.html',
            self.url_names['create']: 'posts/create_post.html',
            self.url_names['post']: 'posts/post_detail.html',
            self.url_names['post_edit']: 'posts/create_post.html',
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response: HttpResponse = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_posts_add_comment_auth_user(self) -> None:
        """Redirect authorized user to post page after comment."""
        response: HttpResponse = self.authorized_client.post(
            f'/posts/{self.another_user_post.pk}/comment/',
            data={'text': 'Комментарий'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/posts/{self.another_user_post.pk}/'
        )

    def test_posts_add_comment_guest(self) -> None:
        """Create a comment may only the authorized user."""
        comments_count: int = Comment.objects.count()
        response: HttpResponse = self.guest_client.post(
            f'/posts/{self.another_user_post.pk}/comment/',
            data={'text': 'Комментарий'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_index_cahce(self) -> None:
        """Test index page cache."""
        response_before_delete = self.guest_client.get('/')
        Post.objects.filter(pk=self.post.pk).delete()
        response_after_delete = self.guest_client.get('/')
        self.assertEqual(
            response_before_delete.content,
            response_after_delete.content
        )
        cache.clear()
        response_after_cache_clear = self.guest_client.get('/')
        self.assertNotEqual(
            response_after_cache_clear.content,
            response_before_delete.content
        )

    def test_follow_auth_user(self) -> None:
        """Authorized user can subscribe to other users and redirect."""
        response: HttpResponse = self.authorized_client.get(
            f'/profile/{self.another_user.username}/follow/'
        )
        self.assertRedirects(
            response,
            f'/profile/{self.another_user.username}/'
        )
        self.assertEqual(
            Follow.objects.filter(user=self.user.id).count(),
            self.follows_count + 1
        )

    def test_unfollow_auth_user(self) -> None:
        """Authorized user can unsubscribe to other users and redirect."""
        response: HttpResponse = self.authorized_client.get(
            f'/profile/{self.another_user.username}/unfollow/'
        )
        self.assertRedirects(
            response,
            f'/profile/{self.another_user.username}/'
        )
        self.assertEqual(
            Follow.objects.filter(user=self.user.id).count(),
            self.follows_count - 1
        )

    def test_new_post_in_follows(self) -> None:
        """New post appears to followers and dont to others."""
        follows: QuerySet[int] = self.user.follower.values_list(
            'author', flat=True
        )
        follows_posts_count: int = Post.objects.filter(
            author_id__in=follows
        ).count()
        other: QuerySet[int] = self.another_user.follower.values_list(
            'author', flat=True
        )
        other_posts_count: int = Post.objects.filter(
            author_id__in=other
        ).count()
        Post.objects.create(
            author=self.another_user,
            text='Делай ноги 2!',
        )
        self.assertEqual(
            Post.objects.filter(author_id__in=follows).count(),
            follows_posts_count + 1
        )
        self.assertEqual(
            other_posts_count, other_posts_count
        )
