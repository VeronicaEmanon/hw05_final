import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, Comment, Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
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
        cls.count = cls.post.author.posts.count()
        cls.form = PostForm()

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

    def test_index_cache(self):
        post_count = Post.objects.count()
        response = self.authorized_client.get('/')
        before_cahce_content = response.content
        Post.objects.get().delete()
        self.assertEqual(Post.objects.count(), post_count - 1)
        after_cache_content = response.content
        self.assertEqual(before_cahce_content, after_cache_content)
        cache.clear()
        after_clear_cache = self.authorized_client.get('/')
        self.assertNotEqual(before_cahce_content, after_clear_cache)

    def test_pages_uses_correct_template(self):
        cache.clear()
        templates_pages = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list', kwargs={'slug': self.group.slug})):
            'posts/group_list.html',
            (reverse('posts:profile', kwargs={'username': self.post.author})):
            'posts/profile.html',
            (reverse('posts:post_detail', kwargs={'post_id': self.post.pk})):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            (reverse('posts:post_edit', kwargs={'post_id': self.post.pk})):
            'posts/post_create.html',
        }

        for reverse_name, template in templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def checking_correct_post(self, post):
        first_object = post
        post = PostViewsTests.post
        task_author_0 = first_object.author
        task_text_0 = first_object.text
        task_group_0 = first_object.group
        task_image_0 = first_object.image
        self.assertEqual(task_author_0, post.author)
        self.assertEqual(task_text_0, post.text)
        self.assertEqual(task_group_0, post.group)
        self.assertEqual(task_image_0, post.image)

    def checking_correct_group(self, group):
        first_object = group
        group = PostViewsTests.group
        task_title_0 = first_object.title
        task_slug_0 = first_object.slug
        task_description_0 = first_object.description
        self.assertEqual(task_title_0, group.title)
        self.assertEqual(task_slug_0, group.slug)
        self.assertEqual(task_description_0, group.description)

    def test_index_page_show_correct_context(self):
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.checking_correct_post(first_object)

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        first_object = response.context.get('group')
        self.checking_correct_group(first_object)
        second_object = response.context.get('page_obj')[0]
        self.checking_correct_post(second_object)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        first_object = response.context.get('page_obj')[0]
        self.checking_correct_post(first_object)
        second_object = response.context.get('count')
        self.assertEqual(second_object, self.count)
        third_object = response.context.get('author')
        self.assertEqual(third_object, self.post.author)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        first_object = response.context.get('post')
        self.checking_correct_post(first_object)
        second_object = response.context.get('count')
        self.assertEqual(second_object, self.count)

    def test_new_post_show_correct_context(self):
        response = self.post_author.get(
            reverse('posts:post_create')
        )
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIsNot(response.context.get('is_edit'), False)

    def test_edit_post_show_correct_context(self):
        response = self.post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        first_object = response.context.get('post')
        self.checking_correct_post(first_object)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get('is_edit'), True)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagintaorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        upload = SimpleUploadedFile(
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
            image=upload,
        )

        cls.post_list = [
            Post(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group,
                image=upload
            )
            for i in range(13)
        ]
        Post.objects.bulk_create(cls.post_list)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_four_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page_obj')), 4)

    def test_first_page_group_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_group_contains_four_records(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 4)

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_first_page_contains_four_records(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
            + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 4)


class CommentViewsTest(TestCase):
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

    def test_comment_post_show_in_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertIsInstance(response.context.get('form'), CommentForm)
        first_object = response.context.get('comments')[0]
        self.assertEqual(first_object, self.comment)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='auth')
        cls.following = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            author=cls.following,
            text='Тестовый пост',
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.follower)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.following)

    def test_follower_author(self):
        count_follow = Follow.objects.filter(user=self.follower).count()
        follow_data = {
            'user': self.follower,
            'author': self.following
        }
        response = self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following}
            ),
            data=follow_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        count_follow2 = Follow.objects.filter(user=self.follower).count()
        self.assertEqual(count_follow2, count_follow + 1)

    def test_unfollow_author(self):
        count_follow = Follow.objects.filter(user=self.follower).count()
        follow_data = {
            'user': self.follower,
            'author': self.following
        }
        response = self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.following}
            ),
            data=follow_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        count_follow2 = Follow.objects.filter(user=self.follower).count()
        self.assertEqual(count_follow2, count_follow)

    def test_post_for_follower(self):
        new_post_for_follower = Post.objects.create(
            author=self.following,
            text='Тестовый пост',
        )
        Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        new_post = response.context.get('page_obj')
        self.assertIn(new_post_for_follower, new_post)

    def test_post_for_unfollower(self):
        new_post_for_follower = Post.objects.create(
            author=self.following,
            text='Тестовый пост',
        )
        Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        new_post = response.context.get('page_obj')
        self.assertNotIn(new_post_for_follower, new_post)
