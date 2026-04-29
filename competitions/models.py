from django.db import models
from users.models import User, AthleteProfile
from branches.models import Branch

class Competition(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Предстоящее'),
        ('ongoing', 'Идёт сейчас'),
        ('finished', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    location = models.CharField(max_length=300, verbose_name='Место проведения')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='competitions', verbose_name='Филиал-организатор')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(blank=True, null=True, verbose_name='Дата окончания')
    registration_deadline = models.DateField(blank=True, null=True, verbose_name='Дедлайн регистрации')
    program = models.TextField(blank=True, verbose_name='Программа соревнований')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming', verbose_name='Статус')
    max_participants = models.PositiveIntegerField(default=0, verbose_name='Максимум участников')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    image = models.ImageField(upload_to='competitions/', blank=True, verbose_name='Баннер')

    def __str__(self):
        return self.title

    def registered_count(self):
        return self.registrations.count()

    class Meta:
        verbose_name = 'Соревнование'
        verbose_name_plural = 'Соревнования'
        ordering = ['start_date']

class Registration(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='registrations', verbose_name='Соревнование')
    athlete = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, verbose_name='Спортсмен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата заявки')
    is_confirmed = models.BooleanField(default=False, verbose_name='Подтверждено')

    def __str__(self):
        return f'{self.athlete.user.get_full_name()} → {self.competition.title}'

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        unique_together = ['competition', 'athlete']

class Result(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='results', verbose_name='Соревнование')
    athlete = models.ForeignKey(AthleteProfile, on_delete=models.CASCADE, verbose_name='Спортсмен')
    discipline = models.CharField(max_length=200, verbose_name='Дисциплина')
    place = models.PositiveIntegerField(blank=True, null=True, verbose_name='Место')
    result_time = models.CharField(max_length=50, blank=True, verbose_name='Результат')
    points = models.PositiveIntegerField(default=0, verbose_name='Очки')

    def __str__(self):
        return f'{self.athlete.user.get_full_name()} — {self.discipline} — {self.place} место'

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
        ordering = ['discipline', 'place']

class BranchScore(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='branch_scores', verbose_name='Соревнование')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name='Филиал')
    total_points = models.PositiveIntegerField(default=0, verbose_name='Очки')
    gold = models.PositiveIntegerField(default=0, verbose_name='Золото')
    silver = models.PositiveIntegerField(default=0, verbose_name='Серебро')
    bronze = models.PositiveIntegerField(default=0, verbose_name='Бронза')

    def __str__(self):
        return f'{self.branch.name}: {self.total_points} очков'

    class Meta:
        verbose_name = 'Зачёт филиала'
        verbose_name_plural = 'Зачёт филиалов'
        unique_together = ['competition', 'branch']
