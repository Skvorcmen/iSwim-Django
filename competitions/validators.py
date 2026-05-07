import re
from django.core.exceptions import ValidationError


def validate_result_time(value):
    """
    Валидирует формат времени: MM:SS.ss или MM:SS.sss
    Примеры корректных значений: 1:23.45, 10:45.67, 2:03.14
    """
    if not value:  # Пустое значение разрешено
        return
    
    # Паттерн: M:SS.ss(s) или MM:SS.ss(s)
    # M(M) - 1-2 цифры (0-59 минуты)
    # SS - 2 цифры (0-59 секунды)
    # ss(s) - 2-3 цифры (сотые/тысячные доли)
    pattern = r'^(\d{1,2}):(\d{2})\.(\d{2,3})$'
    
    if not re.match(pattern, value):
        raise ValidationError(
            'Время должно быть в формате M:SS.ss или MM:SS.ss (например: 1:23.45 или 10:45.67)',
            code='invalid_time_format'
        )
    
    # Проверяем диапазоны
    try:
        minutes, seconds, decimals = re.match(pattern, value).groups()
        minutes = int(minutes)
        seconds = int(seconds)
        
        if seconds > 59:
            raise ValidationError(
                'Секунды не могут быть больше 59',
                code='invalid_seconds'
            )
        
        # Реалистичные границы для плавания (макс ~12 минут на 1500м)
        if minutes > 20:
            raise ValidationError(
                'Время превышает реалистичные границы (макс ~20 минут)',
                code='unrealistic_time'
            )
            
    except (ValueError, AttributeError):
        raise ValidationError(
            'Некорректный формат времени',
            code='invalid_format'
        )


def normalize_result_time(time_str):
    """
    Нормализует строку времени, если она валидна.
    Возвращает True если время корректно, False если нет.
    """
    try:
        validate_result_time(time_str)
        return True
    except ValidationError:
        return False
