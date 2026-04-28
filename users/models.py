from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='Отчество')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='Аватар')

    def __str__(self):
        return self.get_full_name() or self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class AthleteProfile(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Новичок'),
        ('amateur', 'Любитель'),
        ('advanced', 'Продвинутый'),
        ('pro', 'Профессионал'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_profile', verbose_name='Пользователь')
    birth_date = models.DateField(verbose_name='Дата рождения')
    swimming_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner', verbose_name='Уровень')
    medical_notes = models.TextField(blank=True, verbose_name='Мед. противопоказания')
    parent_contact = models.CharField(max_length=20, blank=True, verbose_name='Контакт родителя')

    def __str__(self):
        return f'Спортсмен: {self.user.get_full_name()}'

    class Meta:
        verbose_name = 'Спортсмен'
        verbose_name_plural = 'Спортсмены'

class FanProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fan_profile', verbose_name='Пользователь')
    favorite_athletes = models.ManyToManyField(AthleteProfile, blank=True, verbose_name='Любимые спортсмены')

    def __str__(self):
        return f'Болельщик: {self.user.get_full_name()}'

    class Meta:
        verbose_name = 'Болельщик'
        verbose_name_plural = 'Болельщики'
