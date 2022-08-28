from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group, Comment


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост151515',
            image='posts/small.gif'
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post_id=cls.post.id 
        )

    def test_models_have_correct_object_names(self):
        post = PostModelTest.post
        expenced_object_name = post.text[:15]
        self.assertNotEqual(expenced_object_name, str(post))

    def test_models_group_have_correct_names(self):
        group = PostModelTest.group
        expenced_object_name = group.title
        self.assertEqual(expenced_object_name, str(group))

    def test_text_label(self):
        text_label = Post._meta.get_field('text').verbose_name
        self.assertEqual(text_label, 'Текст поста')

    def test_group_label(self):
        group_label = Post._meta.get_field('group').verbose_name
        self.assertEqual(group_label, 'Группа')

    def test_comment_label(self):
        comment_label = Comment._meta.get_field('post').verbose_name
        self.assertEqual(comment_label, 'Текст комментария')

    def test_text_help_text(self):
        text_help_text = Post._meta.get_field('text').help_text
        self.assertEqual(text_help_text, 'Введите текст поста')

    def test_group_help_text(self):
        group_help_text = Post._meta.get_field('group').help_text
        self.assertEqual(
            group_help_text, 'Выберете группу для своего поста'
        )

    def test_comment_help_text(self):
        comment_help_text = Comment._meta.get_field('post').help_text
        self.assertEqual(
            comment_help_text, 'Введите текст комментария'
        )
