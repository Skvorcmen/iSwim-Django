"""
Сервис для управления рекордами.
Сегментация: по полу + возрасту + дисциплине + стилю + дистанции.
"""
from django.db import transaction
from .models import Record, HeatAssignment
from .services import result_time_to_seconds
import logging

logger = logging.getLogger(__name__)


def get_record_key(assignment):
    """
    Получить ключ для уникального рекорда.
    Ключ: (discipline, gender, age_category)
    """
    athlete = assignment.registration.athlete
    return {
        'discipline': assignment.heat.discipline,
        'gender': athlete.gender,
        'age_category': assignment.heat.age_category,
    }


def time_is_better_than_record(new_time, current_record_time):
    """
    Проверить, лучше ли новое время, чем текущий рекорд.
    Возвращает True если новое время быстрее.
    """
    try:
        new_seconds = result_time_to_seconds(new_time)
        current_seconds = result_time_to_seconds(current_record_time)
        return new_seconds < current_seconds
    except (ValueError, TypeError):
        return False


def get_current_record(discipline, gender, age_category):
    """
    Получить текущий рекорд для дисциплины и категории.
    """
    return Record.objects.filter(
        discipline=discipline,
        gender=gender,
        age_category=age_category,
        is_current=True,
    ).first()


def check_and_update_records(assignment):
    """
    Проверить, установил ли спортсмен новый рекорд.
    Если да:
    - пометить старый рекорд как is_current=False
    - создать новый рекорд с is_current=True
    
    Возвращает: (record_created, is_new_record)
    """
    # Проверяем что финиш был завершен
    if not assignment.result_time or assignment.status != 'finished':
        return None, False
    
    try:
        new_time_seconds = result_time_to_seconds(assignment.result_time)
    except (ValueError, TypeError):
        return None, False
    
    record_key = get_record_key(assignment)
    current_record = get_current_record(**record_key)
    
    # Если нет текущего рекорда - это первый рекорд в этой категории
    if not current_record:
        record = Record.objects.create(
            competition=assignment.heat.competition,
            discipline=record_key['discipline'],
            athlete=assignment.registration.athlete,
            gender=record_key['gender'],
            age_category=record_key['age_category'],
            time=assignment.result_time,
            date_set=assignment.heat.competition.start_date,
            is_current=True,
        )
        logger.info(
            f"First record set: {assignment.registration.athlete.user.get_full_name()} "
            f"— {record_key['discipline']} {assignment.result_time}"
        )
        return record, True
    
    # Сравниваем с текущим рекордом
    try:
        current_time_seconds = result_time_to_seconds(current_record.time)
    except (ValueError, TypeError):
        current_time_seconds = float('inf')
    
    # Если новое время не лучше текущего рекорда - ничего не делаем
    if new_time_seconds >= current_time_seconds:
        logger.debug(
            f"Time {assignment.result_time} is not better than current record "
            f"{current_record.time} for {record_key['discipline']}"
        )
        return None, False
    
    # Новое время лучше - обновляем рекорды
    with transaction.atomic():
        # Помечаем старый рекорд как неактуальный
        current_record.is_current = False
        current_record.save(update_fields=['is_current'])
        
        # Создаем новый рекорд
        new_record = Record.objects.create(
            competition=assignment.heat.competition,
            discipline=record_key['discipline'],
            athlete=assignment.registration.athlete,
            gender=record_key['gender'],
            age_category=record_key['age_category'],
            time=assignment.result_time,
            date_set=assignment.heat.competition.start_date,
            is_current=True,
        )
        
        logger.info(
            f"New record set: {assignment.registration.athlete.user.get_full_name()} "
            f"— {record_key['discipline']} {assignment.result_time} "
            f"(prev: {current_record.time})"
        )
        
        return new_record, True


def check_and_update_all_records(competition):
    """
    Проверить и обновить все рекорды для всех финишировавших спортсменов в соревновании.
    Вызывается после завершения соревнования.
    
    Возвращает список установленных рекордов.
    """
    new_records = []
    
    # Получаем все завершённые заплывы с результатами
    assignments = HeatAssignment.objects.filter(
        heat__competition=competition,
        status='finished',
        result_time__isnull=False,
    ).exclude(result_time='').select_related(
        'registration__athlete__user',
        'heat__discipline',
        'heat__age_category',
        'heat__competition',
    )
    
    for assignment in assignments:
        record, is_new = check_and_update_records(assignment)
        if is_new:
            new_records.append(record)
    
    return new_records


def get_athlete_records(athlete_profile):
    """
    Получить все рекорды спортсмена (только текущие).
    """
    return Record.objects.filter(
        athlete=athlete_profile,
        is_current=True,
    ).select_related('discipline', 'age_category')


def get_discipline_records(discipline, limit=None):
    """
    Получить лучшие рекорды по дисциплине (по полу и возрасту).
    """
    records = Record.objects.filter(
        discipline=discipline,
        is_current=True,
    ).select_related('athlete__user', 'age_category').order_by('time')
    
    if limit:
        records = records[:limit]
    
    return records


def get_leaderboard_for_discipline(discipline, gender=None, age_category=None):
    """
    Получить лидерборд по дисциплине с фильтром по полу/возрасту.
    """
    qs = Record.objects.filter(
        discipline=discipline,
        is_current=True,
    )
    
    if gender:
        qs = qs.filter(gender=gender)
    
    if age_category:
        qs = qs.filter(age_category=age_category)
    
    return qs.select_related('athlete__user', 'age_category').order_by('time')
