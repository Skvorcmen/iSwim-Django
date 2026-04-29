from django.db import models
from users.models import User, AthleteProfile, SecretaryProfile
from branches.models import Branch

class Competition(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Предстоящее'),
        ('registration', 'Регистрация открыта'),
        ('closed', 'Регистрация закрыта'),
        ('ongoing', 'Идёт сейчас'),
        ('finished', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    location = models.CharField(max_length=300, verbose_name='Место проведения')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Филиал')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(blank=True, null=True, verbose_name='Дата окончания')
    registration_deadline = models.DateField(blank=True, null=True, verbose_name='Дедлайн заявок')
    registration_deadline_time = models.CharField(max_length=5, default="23:59", verbose_name="Время закрытия заявок")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='upcoming', verbose_name='Статус')
    lanes = models.PositiveIntegerField(default=6, verbose_name='Количество дорожек')
    regulation = models.FileField(upload_to='regulations/', blank=True, verbose_name='Положение (PDF)')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Создал')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    image = models.ImageField(upload_to='competitions/', blank=True, verbose_name='Баннер')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Соревнование'
        verbose_name_plural = 'Соревнования'
        ordering = ['start_date']

class AgeCategory(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='age_categories', verbose_name='Соревнование')
    name = models.CharField(max_length=100, verbose_name='Название')
    birth_year_from = models.PositiveIntegerField(verbose_name='Год рождения от')
    birth_year_to = models.PositiveIntegerField(verbose_name='Год рождения до')
    gender = models.CharField(max_length=1, choices=[('M', 'Мужчины'), ('F', 'Женщины')], verbose_name='Пол')

    def __str__(self):
        return f'{self.name} ({self.get_gender_display()})'

    class Meta:
        verbose_name = 'Возрастная категория'
        verbose_name_plural = 'Возрастные категории'

class Discipline(models.Model):
    STYLE_CHOICES = [
        ('free', 'Вольный стиль'),
        ('back', 'На спине'),
        ('breast', 'Брасс'),
        ('fly', 'Баттерфляй'),
        ('medley', 'Комплекс'),
    ]
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='disciplines', verbose_name='Соревнование')
    style = models.CharField(max_length=10, choices=STYLE_CHOICES, verbose_name='Стиль')
    distance = models.PositiveIntegerField(verbose_name='Дистанция (м)')

    def __str__(self):
        return f'{self.get_style_display()} {self.distance}м'

    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'
        unique_together = ['competition', 'style', 'distance']

class Registration(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='registrations', verbose_name='Соревнование')
    athlete = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, verbose_name='Спортсмен')
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name='Дисциплина')
    preliminary_time = models.CharField(max_length=20, blank=True, verbose_name='Предварительное время')
    coach = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Тренер')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, verbose_name='Филиал')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заявки')
    is_confirmed = models.BooleanField(default=False, verbose_name='Подтверждено')

    def __str__(self):
        return f'{self.athlete.user.get_full_name()} — {self.discipline}'

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        unique_together = ['competition', 'athlete', 'discipline']

class Heat(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='heats', verbose_name='Соревнование')
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='heats', verbose_name='Дисциплина')
    age_category = models.ForeignKey(AgeCategory, on_delete=models.CASCADE, verbose_name='Возрастная категория')
    number = models.PositiveIntegerField(verbose_name='Номер заплыва')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    def __str__(self):
        return f'Заплыв {self.number} — {self.discipline}'

    class Meta:
        verbose_name = 'Заплыв'
        verbose_name_plural = 'Заплывы'
        ordering = ['number']

class HeatAssignment(models.Model):
    heat = models.ForeignKey(Heat, on_delete=models.CASCADE, related_name='assignments', verbose_name='Заплыв')
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, verbose_name='Заявка')
    lane = models.PositiveIntegerField(verbose_name='Дорожка')
    result_time = models.CharField(max_length=20, blank=True, verbose_name='Результат')
    place = models.PositiveIntegerField(blank=True, null=True, verbose_name='Место')

    def __str__(self):
        return f'{self.registration.athlete.user.get_full_name()} — Дорожка {self.lane}'

    class Meta:
        verbose_name = 'Назначение в заплыв'
        verbose_name_plural = 'Назначения в заплывы'
        unique_together = ['heat', 'lane']

from datetime import datetime, date

def check_registration_deadline(competition):
    if competition.status == 'upcoming' and competition.registration_deadline:
        now = datetime.now()
        d = competition.registration_deadline
        t = competition.registration_deadline_time or '23:59'
        h, m = map(int, t.split(':'))
        deadline = datetime(d.year, d.month, d.day, h, m)
        if now > deadline:
            competition.status = 'closed'
            competition.save()
