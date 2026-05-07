from django.db import models

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='ЧПУ')
    image = models.ImageField(upload_to='news/', blank=True, verbose_name='Изображение')
    short_text = models.TextField(verbose_name='Краткий текст')
    full_text = models.TextField(verbose_name='Полный текст')
    published_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, related_name='news', null=True, blank=True, verbose_name='Соревнование')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']
from users.models import User

class NewsComment(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='comments', verbose_name='Новость')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    text = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    def __str__(self):
        return f'{self.user}: {self.text[:30]}'

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

class NewsLike(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='likes', verbose_name='Новость')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    def __str__(self):
        return f'{self.user} лайкнул {self.news}'

    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ['news', 'user']
