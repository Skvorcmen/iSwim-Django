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
    gender = models.CharField(max_length=1, choices=[("M", "Мужчина"), ("F", "Женщина")], default="M", verbose_name="Пол")
    instagram_url = models.URLField(blank=True, verbose_name='Instagram')
    experience_years = models.PositiveIntegerField(blank=True, null=True, verbose_name='Стаж плавания (лет)')
    medical_notes = models.TextField(blank=True, verbose_name='Мед. противопоказания')
    parent_contact = models.CharField(max_length=20, blank=True, verbose_name='Контакт родителя')

    def __str__(self):
        return f'Спортсмен: {self.user.get_full_name()}'

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

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

class Achievement(models.Model):
    ACHIEVEMENT_TYPES = [
        ('record', 'Рекорд школы'),
        ('medal', 'Медаль'),
        ('rank', 'Разряд'),
        ('other', 'Другое'),
    ]
    athlete = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, related_name='achievements', verbose_name='Спортсмен')
    title = models.CharField(max_length=200, verbose_name='Название')
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES, verbose_name='Тип')
    description = models.TextField(blank=True, verbose_name='Описание')
    competition = models.CharField(max_length=200, blank=True, verbose_name='Соревнование')
    date = models.DateField(verbose_name='Дата')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    def __str__(self):
        return f'{self.athlete}: {self.title}'

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['-date']

class SecretaryProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='secretary_profile', verbose_name='Пользователь')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    def __str__(self):
        return f'Секретарь: {self.user.get_full_name()}'

    class Meta:
        verbose_name = 'Секретарь'
        verbose_name_plural = 'Секретари'
# Добавлено поле gender в AthleteProfile
