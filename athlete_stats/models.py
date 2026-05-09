from django.db import models
from users.models import AthleteProfile
from competitions.models import Competition, Discipline


class PersonalRecord(models.Model):
    athlete = models.ForeignKey(
        AthleteProfile, on_delete=models.CASCADE,
        related_name='personal_records', verbose_name='Спортсмен'
    )
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE,
        related_name='personal_records', verbose_name='Дисциплина'
    )
    competition = models.ForeignKey(
        Competition, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Соревнование'
    )
    result_time = models.CharField(max_length=20, verbose_name='Результат')
    result_seconds = models.FloatField(verbose_name='Результат (сек)', default=0)
    date = models.DateField(verbose_name='Дата')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Личный рекорд'
        verbose_name_plural = 'Личные рекорды'
        ordering = ['discipline', 'result_seconds']

    def __str__(self):
        return f'{self.athlete} — {self.discipline} — {self.result_time}'


class AthleteResult(models.Model):
    athlete = models.ForeignKey(
        AthleteProfile, on_delete=models.CASCADE,
        related_name='results', verbose_name='Спортсмен'
    )
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE,
        related_name='athlete_results', verbose_name='Дисциплина'
    )
    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE,
        verbose_name='Соревнование'
    )
    result_time = models.CharField(max_length=20, verbose_name='Результат')
    result_seconds = models.FloatField(verbose_name='Результат (сек)')
    place = models.PositiveIntegerField(null=True, blank=True, verbose_name='Место')
    date = models.DateField(verbose_name='Дата')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Результат спортсмена'
        verbose_name_plural = 'Результаты спортсменов'
        ordering = ['date']
        unique_together = ['athlete', 'discipline', 'competition']

    def __str__(self):
        return f'{self.athlete} — {self.discipline} — {self.result_time}'
