from django.db import models
from users.models import User
from branches.models import Branch

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile', verbose_name='Пользователь')
    bio = models.TextField(verbose_name='О себе')
    experience_years = models.PositiveIntegerField(verbose_name='Стаж (лет)')
    specialization = models.CharField(max_length=200, verbose_name='Специализация')
    photo = models.ImageField(upload_to='trainers/', verbose_name='Фото')
    branches = models.ManyToManyField(Branch, related_name='trainers', verbose_name='Филиалы')
    certifications = models.TextField(blank=True, verbose_name='Сертификаты и лицензии')
    programs = models.TextField(blank=True, verbose_name='Программы и услуги')
    schedule = models.TextField(blank=True, verbose_name='График работы / расписание')
    whatsapp_url = models.URLField(blank=True, verbose_name='WhatsApp')
    instagram_url = models.URLField(blank=True, verbose_name='Instagram')
    rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True, verbose_name='Рейтинг')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return self.user.get_full_name()

    @property
    def rating_display(self):
        return f'{self.rating:.1f}/5' if self.rating else 'Нет оценки'

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'
