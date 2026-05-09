# Добавь в конец файла (перед последней скобкой)

def health_check(request):
    """Безопасная проверка здоровья сервера"""
    import os
    from django.http import JsonResponse
    
    # Проверяем наличие переменных (не показываем их значения!)
    has_secret = bool(os.environ.get('SECRET_KEY'))
    has_debug = 'DEBUG' in os.environ
    has_hosts = 'ALLOWED_HOSTS' in os.environ
    
    # Получаем имя базы данных (безопасно)
    from django.conf import settings
    db_name = settings.DATABASES['default'].get('NAME', 'unknown')
    db_engine = settings.DATABASES['default']['ENGINE']
    
    return JsonResponse({
        'status': 'ok',
        'database': db_engine,
        'database_name': str(db_name),
        'has_secret_key': has_secret,
        'has_debug_var': has_debug,
        'has_hosts_var': has_hosts,
        'debug_mode': settings.DEBUG,
    })
