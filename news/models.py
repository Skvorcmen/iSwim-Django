from django.db import models

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='ЧПУ')
    image = models.ImageField(upload_to='news/', verbose_name='Изображение')
    short_text = models.TextField(verbose_name='Краткий текст')
    full_text = models.TextField(verbose_name='Полный текст')
    published_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']
