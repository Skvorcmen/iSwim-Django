from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Competition, Registration, Result, BranchScore
from users.models import AthleteProfile
from activity.models import Activity
from django.utils import timezone

class CompetitionListView(ListView):
    model = Competition
    template_name = 'competitions/competition_list.html'
    context_object_name = 'competitions'

    def get_queryset(self):
        filter_status = self.request.GET.get('status', '')
        if filter_status:
            return Competition.objects.filter(status=filter_status)
        return Competition.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upcoming'] = Competition.objects.filter(status='upcoming')
        context['ongoing'] = Competition.objects.filter(status='ongoing')
        context['finished'] = Competition.objects.filter(status='finished').order_by('-start_date')[:10]
        context['current_filter'] = self.request.GET.get('status', '')
        return context

class CompetitionDetailView(DetailView):
    model = Competition
    template_name = 'competitions/competition_detail.html'
    context_object_name = 'comp'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['registrations'] = self.object.registrations.filter(is_confirmed=True)
        context['results'] = self.object.results.all().order_by('discipline', 'place')
        context['branch_scores'] = self.object.branch_scores.all().order_by('-total_points')
        if self.request.user.is_authenticated and hasattr(self.request.user, 'athlete_profile'):
            context['is_registered'] = self.object.registrations.filter(
                athlete=self.request.user.athlete_profile
            ).exists()
        return context

@login_required
def register_for_competition(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    if not hasattr(request.user, 'athlete_profile'):
        messages.error(request, 'Только спортсмены могут подавать заявки')
        return redirect('competition_detail', pk=pk)
    
    if comp.status != 'upcoming':
        messages.error(request, 'Регистрация закрыта')
        return redirect('competition_detail', pk=pk)
    
    athlete = request.user.athlete_profile
    reg, created = Registration.objects.get_or_create(competition=comp, athlete=athlete)
    if created:
        Activity.objects.create(
            user=request.user,
            activity_type='competition',
            title=f'{request.user.get_full_name()} зарегистрировался на соревнование «{comp.title}»',
            link=f'/competitions/{comp.pk}/'
        )
    messages.success(request, 'Заявка принята!')
    return redirect('competition_detail', pk=pk)

@login_required
def unregister_from_competition(request, pk):
    comp = get_object_or_404(Competition, pk=pk)
    athlete = request.user.athlete_profile
    Registration.objects.filter(competition=comp, athlete=athlete).delete()
    return redirect('competition_detail', pk=pk)

class BranchRatingView(ListView):
    template_name = 'competitions/branch_rating.html'
    context_object_name = 'scores'
    model = BranchScore

    def get_queryset(self):
        return BranchScore.objects.values('branch__name').annotate(
            total=Sum('total_points'),
            gold=Sum('gold'),
            silver=Sum('silver'),
            bronze=Sum('bronze')
        ).order_by('-total')
