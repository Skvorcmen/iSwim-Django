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

# Добавляем недостающие классы в начало файла
from django.views.generic import ListView, DetailView, CreateView
from .models import Competition

class CompetitionListView(ListView):
    model = Competition
    template_name = 'competitions/competition_list.html'
    context_object_name = 'competitions'

class CompetitionDetailView(DetailView):
    model = Competition
    template_name = 'competitions/competition_detail.html'
    context_object_name = 'comp'

class CompetitionCreateView(CreateView):
    model = Competition
    template_name = 'competitions/competition_form.html'
    fields = ['title', 'description', 'location', 'start_date', 'end_date', 'status']

class PublicResultsView(DetailView):
    model = Competition
    template_name = 'competitions/public_results.html'
    context_object_name = 'comp'

class LiveCompetitionView(DetailView):
    model = Competition
    template_name = 'competitions/live_competition.html'
    context_object_name = 'comp'
