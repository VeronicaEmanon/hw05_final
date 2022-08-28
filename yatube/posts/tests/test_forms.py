import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from http import HTTPStatus

from posts.forms import PostForm
from posts.models import Post, Group, Comment
from posts.models import User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.post.author)

    def test_new_post(self):
        post_count = Post.objects.count()
        IMAGE = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        upload = SimpleUploadedFile(
            name='big.gif',
            content=IMAGE,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': upload,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/big.gif'
            ).exists()
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        IMAGE = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x0C'
        )
        upload = SimpleUploadedFile(
            name='small.gif',
            content=IMAGE,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост2',
            'group': self.group2.id,
            'image': upload,
        }
        response = self.post_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id},))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(Post.objects.first().author, self.post.author)
        self.assertEqual(Post.objects.first().text, 'Тестовый пост2')
        self.assertEqual(Post.objects.first().group, self.group2)
        self.assertEqual(Post.objects.first().id, self.post.id)
        self.assertTrue(Post.objects.first().image, 'posts/small.gif')

    def test_new_post_correct_forms_fields(self):
        response = self.post_author.get(
            reverse('posts:post_create')
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get('form').fields[value]
                self.assertIsInstance(form_fields, expected)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post_id=cls.post.id
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'post_id': 'self.post.id',
            'text': 'комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
