from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    address = models.TextField(verbose_name='Адрес')
    map_link = models.URLField(blank=True, verbose_name='Ссылка на карту')
    photo = models.ImageField(upload_to='branches/', verbose_name='Фото')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    schedule = models.TextField(verbose_name='Расписание работы')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
