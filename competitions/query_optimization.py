"""
Оптимизация запросов - исправление N+1 query issues.
"""
from django.db.models import Exists, OuterRef, Q
from .models import HeatAssignment


def get_grouped_heats_optimized(comp):
    """
    Оптимизированная версия get_grouped_heats.
    Использует select_related и prefetch_related для минимизации запросов.
    """
    from .models import Heat
    
    # Загружаем все heats с необходимыми связями за один запрос
    heats = Heat.objects.filter(
        competition=comp
    ).select_related(
        'age_category',  # Избегаем N+1 для age_category
        'discipline'     # Избегаем N+1 для discipline
    ).order_by(
        'age_category__birth_year_from',
        'age_category__gender',
        'discipline__style',
        'discipline__distance',
        'number'
    )
    
    # Проверяем какие дисциплины/категории финализированы
    # Делаем это в памяти вместо N запросов
    finalized_keys = set()
    
    if heats.exists():
        # Получаем все места в один запрос
        finalized_assignments = HeatAssignment.objects.filter(
            heat__competition=comp,
            place__isnull=False
        ).values_list('heat__discipline_id', 'heat__age_category_id').distinct()
        
        finalized_keys = set(finalized_assignments)
    
    # Группируем heats в памяти
    groups = []
    current_key = None
    
    for h in heats:
        key = (h.age_category.id, h.discipline.id)
        if key != current_key:
            current_key = key
            is_finished = key in finalized_keys
            
            groups.append({
                'category': h.age_category,
                'discipline': h.discipline,
                'comp': comp,
                'heats': [],
                'is_finished': is_finished
            })
        
        groups[-1]['heats'].append(h)
    
    return groups


def get_heat_assignments_optimized(heat):
    """
    Получить все assignments для заплыва с оптимизацией.
    """
    return HeatAssignment.objects.filter(
        heat=heat
    ).select_related(
        'registration__athlete__user',
        'registration__branch',
        'heat__discipline'
    ).order_by('lane')


def get_competition_results_optimized(competition):
    """
    Получить результаты соревнования с оптимизацией.
    Используется на странице результатов.
    """
    from .models import Heat
    
    return Heat.objects.filter(
        competition=competition
    ).select_related(
        'age_category',
        'discipline'
    ).prefetch_related(
        'assignments__registration__athlete__user',
    ).order_by('number')


def get_discipline_results_optimized(competition, discipline, age_category):
    """
    Получить результаты для конкретной дисциплины/категории.
    """
    from .models import HeatAssignment
    
    return HeatAssignment.objects.filter(
        heat__competition=competition,
        heat__discipline=discipline,
        heat__age_category=age_category,
        place__isnull=False
    ).select_related(
        'registration__athlete__user',
        'registration__coach',
        'registration__branch',
        'heat__discipline'
    ).order_by('place')


def get_athlete_profile_with_records(athlete):
    """
    Получить профиль спортсмена со всеми рекордами.
    """
    from .models import Record
    
    records = Record.objects.filter(
        athlete=athlete,
        is_current=True
    ).select_related(
        'discipline',
        'age_category'
    )
    
    return {
        'athlete': athlete,
        'records': list(records)
    }


def prefetch_competition_data(competition):
    """
    Предварительная загрузка всех данных соревнования.
    Вызывается один раз при входе на страницу соревнования.
    """
    from .models import Heat, Discipline, AgeCategory
    
    # Загружаем и кэшируем все необходимое
    disciplines = Discipline.objects.filter(
        competition=competition
    ).prefetch_related('heats')
    
    age_categories = AgeCategory.objects.filter(
        competition=competition
    ).prefetch_related('heats')
    
    heats = get_competition_results_optimized(competition)
    
    return {
        'disciplines': list(disciplines),
        'age_categories': list(age_categories),
        'heats': list(heats),
    }
