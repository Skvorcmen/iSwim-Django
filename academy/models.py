from django.db import models

class Article(models.Model):
    CATEGORY_CHOICES = [
        ('technique', 'Техника плавания'),
        ('health', 'Здоровье'),
        ('nutrition', 'Питание'),
    ]
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='ЧПУ')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Категория')
    content = models.TextField(verbose_name='Содержание')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    image = models.ImageField(upload_to='academy/', blank=True, verbose_name='Изображение')
    published_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-published_at']
from users.models import User

class ArticleComment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', verbose_name='Статья')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    text = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    def __str__(self):
        return f'{self.user}: {self.text[:30]}'

    class Meta:
        verbose_name = 'Комментарий статьи'
        verbose_name_plural = 'Комментарии статей'
        ordering = ['-created_at']

class ArticleLike(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes', verbose_name='Статья')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    def __str__(self):
        return f'{self.user} лайкнул {self.article}'

    class Meta:
        verbose_name = 'Лайк статьи'
        verbose_name_plural = 'Лайки статей'
        unique_together = ['article', 'user']
