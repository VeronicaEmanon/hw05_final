import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from http import HTTPStatus


from posts.models import Post, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()
IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.upload = SimpleUploadedFile(
            name='small.gif',
            content=IMAGE,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.upload,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post_id=cls.post.id 
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.post.author)

    def test_urls_uses_correct(self):
        urls = {
            '/',
            f'/group/{self.post.group.slug}/',
            f'/profile/{self.post.author}/',
            f'/posts/{self.post.id}/',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_at_desired_location(self):
        response = self.post_author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_at_desired_location(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_url_at_desired_location(self):
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_for_guest_error(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_post_guest_error(self):
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fposts%2F1%2Fedit%2F'
        )

    def test_edit_authorized_client_error(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            '/posts/1/'
        )

    def test_follow_guest_client_error(self):
        response = self.guest_client.get('/follow/', follow=True)
        self.assertRedirects(
            response, 
            '/auth/login/?next=%2Ffollow%2F'
        )

    
    def test_comment_post_for_guest_client_error(self):
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/',
            follow = True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F'
        )

    def test_urls_uses_correct_template(self):
        cache.clear()
        template_url = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/nonexist-page/': 'core/404.html',
            '/follow/': 'posts/follow.html',
        }
        for url, templates in template_url.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, templates)
