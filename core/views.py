from django.shortcuts import render
from activity.models import Activity
from django.http import JsonResponse
from users.models import AthleteProfile
from trainers.models import Trainer
from branches.models import Branch

def index(request):
    activities = Activity.objects.all()[:5]
    return render(request, 'core/index.html', {'activities': activities})

def search(request):
    query = request.GET.get('q', '').strip().lower()
    results = []
    if len(query) >= 2:
        # Спортсмены
        for a in AthleteProfile.objects.select_related('user').all():
            name = a.user.get_full_name().lower()
            if query in name:
                results.append({
                    'type': 'Спортсмен',
                    'name': a.user.get_full_name(),
                    'url': f'/athlete/{a.user.username}/',
                    'detail': a.get_swimming_level_display(),
                })
                if len(results) >= 5:
                    break

        # Тренеры
        for t in Trainer.objects.select_related('user').all():
            name = t.user.get_full_name().lower()
            spec = t.specialization.lower()
            if query in name or query in spec:
                results.append({
                    'type': 'Тренер',
                    'name': t.user.get_full_name(),
                    'url': f'/trainers/{t.pk}/',
                    'detail': t.specialization,
                })
                if len(results) >= 10:
                    break

        # Филиалы
        for b in Branch.objects.all():
            name = b.name.lower()
            addr = b.address.lower()
            if query in name or query in addr:
                results.append({
                    'type': 'Филиал',
                    'name': b.name,
                    'url': f'/branches/{b.pk}/',
                    'detail': b.address,
                })
                if len(results) >= 15:
                    break

    return JsonResponse({'results': results[:15]})
