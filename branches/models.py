from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    address = models.TextField(verbose_name='Адрес')
    map_link = models.URLField(blank=True, verbose_name='Ссылка на карту')
    photo = models.ImageField(upload_to='branches/', verbose_name='Фото')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    schedule = models.TextField(verbose_name='Расписание работы')
    social_links = models.JSONField(blank=True, null=True, verbose_name='Социальные сети')  # {'vk': 'url', 'telegram': 'url'}
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'

class BranchComment(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='comments', verbose_name='Филиал')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'Комментарий от {self.user.username} к {self.branch.name}'

    class Meta:
        verbose_name = 'Комментарий к филиалу'
        verbose_name_plural = 'Комментарии к филиалам'
