import json
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import User, AthleteProfile
from .models import AthleteResult, PersonalRecord


class AthleteStatsView(LoginRequiredMixin, TemplateView):
    template_name = 'athlete_stats/stats.html'

    def dispatch(self, request, *args, **kwargs):
        username = self.kwargs.get('username')
        
        if username:
            try:
                self.athlete = AthleteProfile.objects.select_related('user').get(user__username=username)
            except AthleteProfile.DoesNotExist:
                messages.error(request, f'Спортсмен с именем {username} не найден')
                return redirect('home')
        else:
            try:
                self.athlete = AthleteProfile.objects.select_related('user').get(user=request.user)
            except AthleteProfile.DoesNotExist:
                messages.warning(request, 'У вас нет профиля спортсмена. Обратитесь к администратору.')
                return redirect('profile')
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        personal_records = PersonalRecord.objects.filter(
            athlete=self.athlete
        ).select_related('discipline', 'competition').order_by(
            'discipline__style', 'discipline__distance'
        )

        disciplines = list(
            AthleteResult.objects.filter(athlete=self.athlete)
            .values('discipline__id', 'discipline__style', 'discipline__distance')
            .distinct()
            .order_by('discipline__distance')
        )

        all_results = AthleteResult.objects.filter(athlete=self.athlete)
        total_competitions = all_results.values('competition').distinct().count()
        medals = {
            'gold': all_results.filter(place=1).count(),
            'silver': all_results.filter(place=2).count(),
            'bronze': all_results.filter(place=3).count(),
        }

        ctx.update({
            'athlete': self.athlete,
            'personal_records': personal_records,
            'disciplines': disciplines,
            'total_competitions': total_competitions,
            'medals': medals,
            'disciplines_json': json.dumps([
                {
                    'id': d['discipline__id'],
                    'label': f"{d['discipline__style']} {d['discipline__distance']}м",
                }
                for d in disciplines
            ]),
        })
        return ctx


def progress_data(request, athlete_id, discipline_id):
    results = AthleteResult.objects.filter(
        athlete_id=athlete_id,
        discipline_id=discipline_id,
    ).select_related('competition').order_by('date')

    data = [
        {
            'date': str(r.date),
            'seconds': round(r.result_seconds, 2),
            'time': r.result_time,
            'competition': r.competition.title,
            'place': r.place,
        }
        for r in results
    ]
    return JsonResponse({'data': data})
