from django.contrib.auth import get_user_model
from django.db import models
from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, max_length=50)
    description = models.TextField(verbose_name='Описание группы')

    class Meta:
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='Группа',
        related_name='posts',
        help_text='Выберете группу для своего поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        help_text='Вставьте изображение',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date'),
        verbose_name = 'Пост',
        verbose_name_plural = 'Посты',

    def __str__(self):
        return self.text


class Comment(CreatedModel):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True,
        related_name='comments',
        verbose_name='Автор'
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Текст комментария',
        help_text='Введите текст комментария',
        blank=True
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )

    class Meta:
        ordering = ('-pub_date'),
        verbose_name = 'Комментарий',
        verbose_name_plural = 'Комментарии',

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка',
        verbose_name_plural = 'Подписки',
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'], name='unique_members')]
