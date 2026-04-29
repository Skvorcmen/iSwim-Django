from django.db import models
from users.models import User

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('achievement', 'Достижение'),
        ('competition', 'Соревнование'),
        ('record', 'Рекорд'),
        ('photo', 'Фото'),
        ('other', 'Другое'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name='Пользователь')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name='Тип')
    title = models.CharField(max_length=300, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')
    link = models.CharField(max_length=500, blank=True, verbose_name='Ссылка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Активность'
        verbose_name_plural = 'Активности'
        ordering = ['-created_at']
