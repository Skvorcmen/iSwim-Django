from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from datetime import datetime
from .models import Competition, HeatAssignment
from news.models import News
import re


def time_to_seconds(time_str):
    """Convert time string (MM:SS.ss) to seconds for comparison"""
    try:
        if not time_str or ':' not in time_str:
            return float('inf')
        parts = time_str.split(':')
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    except (ValueError, IndexError):
        return float('inf')


@receiver(post_save, sender=Competition)
def generate_competition_news(sender, instance, created=False, update_fields=None, **kwargs):
    """
    Генерирует новости после завершения соревнования.
    Создает 2-3 новости:
    1. Основная новость с общей информацией
    2. Новость о лучших спортсменах и рекордах
    3. (опционально) Интересные факты
    """
    # Генерируем новости только при переходе в статус 'finished'
    if instance.status != 'finished':
        return
    
    # Проверяем, чтобы новость еще не была создана
    if instance.news.exists():
        return
    
    try:
        # Собираем статистику
        all_assignments = HeatAssignment.objects.filter(
            heat__competition=instance
        ).select_related('registration__athlete__user', 'heat__discipline')
        
        # Находим медалистов и рекордсменов
        medals = {}  # {(discipline, gender): [(place, athlete, time), ...]}
        fastest_times = {}  # {(discipline, gender): time}
        
        for assignment in all_assignments.filter(place__lte=3).order_by('heat__discipline', 'place'):
            if assignment.place is None:
                continue
            
            discipline_key = (
                assignment.heat.discipline.get_style_display(),
                assignment.heat.discipline.distance
            )
            
            if discipline_key not in medals:
                medals[discipline_key] = []
            
            athlete = assignment.registration.athlete.user.get_full_name()
            place_medals = {1: '🥇', 2: '🥈', 3: '🥉'}
            medal = place_medals.get(assignment.place, '')
            
            medals[discipline_key].append({
                'place': assignment.place,
                'medal': medal,
                'athlete': athlete,
                'time': assignment.result_time
            })
        
        # Ищем рекорды (самые быстрые времена)
        for assignment in all_assignments.filter(result_time__isnull=False).exclude(result_time=''):
            discipline_key = (
                assignment.heat.discipline.get_style_display(),
                assignment.heat.discipline.distance
            )
            
            current_time = time_to_seconds(assignment.result_time)
            best_time = time_to_seconds(fastest_times.get(discipline_key, '99:99.99'))
            
            if current_time < best_time:
                fastest_times[discipline_key] = assignment.result_time
        
        # Создаем основную новость с результатами
        main_title = f"Результаты соревнований: {instance.title}"
        main_slug = slugify(f"{main_title}-{instance.start_date}")
        
        main_short_text = f"Соревнование завершено! Участвовало {all_assignments.filter(place__isnull=False).values('registration__athlete').distinct().count()} спортсменов."
        
        # Формируем полный текст с результатами
        main_full_text = f"<h2>Итоги соревнований</h2>\n"
        main_full_text += f"<p><strong>Название:</strong> {instance.title}</p>\n"
        main_full_text += f"<p><strong>Дата:</strong> {instance.start_date}</p>\n"
        main_full_text += f"<p><strong>Место:</strong> {instance.location}</p>\n\n"
        
        # Добавляем медалистов
        main_full_text += "<h3>Победители и призеры:</h3>\n"
        for disc_key, medalists in sorted(medals.items()):
            style_name, distance = disc_key
            main_full_text += f"<h4>{style_name} {distance}м</h4>\n<ul>\n"
            for med in medalists:
                main_full_text += f"<li>{med['medal']} Место {med['place']}: {med['athlete']} ({med['time']})</li>\n"
            main_full_text += "</ul>\n"
        
        # Добавляем рекорды
        if fastest_times:
            main_full_text += "<h3>Рекорды дистанций:</h3>\n<ul>\n"
            for disc_key, time in sorted(fastest_times.items()):
                style_name, distance = disc_key
                main_full_text += f"<li><strong>{style_name} {distance}м:</strong> {time}</li>\n"
            main_full_text += "</ul>\n"
        
        # Создаем основную новость
        News.objects.get_or_create(
            competition=instance,
            title=main_title,
            defaults={
                'slug': main_slug,
                'short_text': main_short_text,
                'full_text': main_full_text,
                'is_published': True,
            }
        )
        
    except Exception as e:
        # Логируем ошибку но не падаем
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating news for competition {instance.pk}: {str(e)}")
