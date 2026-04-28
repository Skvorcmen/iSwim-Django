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
