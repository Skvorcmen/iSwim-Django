from django.db import models
from users.models import User

class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('private', 'Личный'),
        ('group', 'Групповой'),
    ]
    name = models.CharField(max_length=100, verbose_name='Название')
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='private', verbose_name='Тип')
    participants = models.ManyToManyField(User, related_name='chat_rooms', verbose_name='Участники')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', verbose_name='Создатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    avatar = models.ImageField(upload_to='chat_avatars/', blank=True, verbose_name='Аватар')

    def __str__(self):
        return self.name

    def last_message(self):
        return self.messages.last()

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name='Чат')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages', verbose_name='Отправитель')
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')

    def __str__(self):
        return f'{self.sender}: {self.text[:30]}'

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
