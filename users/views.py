from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Count
from users.auth import get_user_role, has_role
from .models import AthleteProfile, FanProfile, Achievement, SecretaryProfile
from branches.models import Branch
from competitions.models import Registration
from trainers.models import Trainer

@login_required
def profile_redirect(request):
    user = request.user
    role = get_user_role(user)
    if role == 'admin':
        return render(request, 'users/admin_profile.html')
    if role == 'trainer':
        return redirect('trainer_profile')
    elif role == 'athlete':
        return redirect('athlete_profile')
    elif role == 'fan':
        return redirect('fan_profile')
    return render(request, 'users/profile_choice.html')

class AthleteProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/athlete_cabinet.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = self.request.user.athlete_profile
        ctx['profile'] = profile
        ctx['achievements'] = profile.achievements.order_by('-date')[:6]
        ctx['achievements_count'] = profile.achievements.count()
        ctx['medal_count'] = profile.achievements.filter(achievement_type='medal').count()
        ctx['record_count'] = profile.achievements.filter(achievement_type='record').count()
        registrations = profile.registration_set.select_related('competition', 'coach', 'branch', 'discipline').order_by('-competition__start_date')
        ctx['upcoming_competitions'] = registrations.filter(is_confirmed=True, competition__start_date__gte=date.today())[:5]
        ctx['competitions_count'] = registrations.count()
        ctx['current_registration'] = registrations.filter(is_confirmed=True).first() or registrations.first()
        ctx['current_coach'] = ctx['current_registration'].coach.trainer_profile if ctx['current_registration'] else None
        ctx['current_branch'] = ctx['current_registration'].branch if ctx['current_registration'] else None
        return ctx

class FanProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/fan_cabinet.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fan_profile = getattr(self.request.user, 'fan_profile', None)
        favorite_athletes = fan_profile.favorite_athletes.all() if fan_profile else AthleteProfile.objects.none()
        ctx['favorite_athletes'] = favorite_athletes
        ctx['favorite_count'] = favorite_athletes.count()
        ctx['favorite_competitions'] = Registration.objects.filter(
            athlete__in=favorite_athletes,
            competition__start_date__gte=date.today()
        ).select_related('competition', 'athlete').order_by('competition__start_date')[:5]
        ctx['upcoming_competitions'] = ctx['favorite_competitions']
        from users.models import Achievement
        ctx['recent_achievements'] = Achievement.objects.filter(
            athlete__in=favorite_athletes
        ).order_by('-date')[:6]
        ctx['total_achievements'] = Achievement.objects.filter(athlete__in=favorite_athletes).count()
        ctx['total_medals'] = Achievement.objects.filter(athlete__in=favorite_athletes, achievement_type='medal').count()
        return ctx

class TrainerProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/trainer_cabinet.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        trainer = self.request.user.trainer_profile
        ctx['trainer'] = trainer
        ctx['branches'] = trainer.branches.all()
        ctx['branches_count'] = trainer.branches.count()
        students = AthleteProfile.objects.filter(
            registration__coach=self.request.user
        ).distinct()
        ctx['students'] = students
        ctx['students_count'] = students.count()
        ctx['upcoming_competitions'] = Registration.objects.filter(
            coach=self.request.user,
            competition__start_date__gte=date.today()
        ).select_related('competition', 'athlete', 'discipline').order_by('competition__start_date')[:5]
        ctx['upcoming_competitions_count'] = Registration.objects.filter(
            coach=self.request.user,
            competition__start_date__gte=date.today()
        ).values('competition').distinct().count()
        return ctx

class WallOfFameView(ListView):
    template_name = 'users/wall_of_fame.html'
    context_object_name = 'athletes'
    def get_queryset(self):
        return AthleteProfile.objects.annotate(achievement_count=Count('achievements')).filter(achievement_count__gt=0).order_by('-achievement_count')[:20]
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['records'] = Achievement.objects.filter(achievement_type='record').order_by('-date')[:10]
        return ctx

class PublicAthleteView(DetailView):
    model = AthleteProfile
    template_name = 'users/public_athlete.html'
    context_object_name = 'athlete'
    slug_field = 'user__username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['achievements'] = self.object.achievements.order_by('-date')[:10]
        ctx['medal_count'] = self.object.achievements.filter(achievement_type='medal').count()
        ctx['record_count'] = self.object.achievements.filter(achievement_type='record').count()
        registrations = self.object.registration_set.select_related('competition', 'coach', 'branch', 'discipline').order_by('-competition__start_date')
        ctx['recent_competitions'] = registrations[:5]
        ctx['current_registration'] = registrations.filter(is_confirmed=True).first() or registrations.first()
        ctx['current_coach'] = ctx['current_registration'].coach if ctx['current_registration'] else None
        ctx['current_branch'] = ctx['current_registration'].branch if ctx['current_registration'] else None
        ctx['current_discipline'] = ctx['current_registration'].discipline if ctx['current_registration'] else None
        ctx['training_branches'] = Branch.objects.filter(id__in=self.object.registration_set.values_list('branch_id', flat=True)).distinct()
        ctx['training_coaches'] = Trainer.objects.filter(user__in=self.object.registration_set.values_list('coach_id', flat=True)).distinct()
        return ctx

class PublicFanView(DetailView):
    model = FanProfile
    template_name = 'users/public_fan.html'
    context_object_name = 'fan'
    slug_field = 'user__username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['favorite_athletes'] = self.object.favorite_athletes.all()
        ctx['favorite_count'] = ctx['favorite_athletes'].count()
        ctx['favorite_competitions'] = Registration.objects.filter(
            athlete__in=ctx['favorite_athletes'],
            competition__start_date__gte=date.today()
        ).select_related('competition', 'athlete').order_by('competition__start_date')[:5]
        return ctx

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()
        
        trainer_profile = getattr(user, 'trainer_profile', None)
        if has_role(user, 'trainer') and trainer_profile:
            trainer_profile.bio = request.POST.get('bio', trainer_profile.bio)
            trainer_profile.specialization = request.POST.get('specialization', trainer_profile.specialization)
            trainer_profile.experience_years = request.POST.get('experience_years', trainer_profile.experience_years)
            trainer_profile.programs = request.POST.get('programs', trainer_profile.programs)
            trainer_profile.certifications = request.POST.get('certifications', trainer_profile.certifications)
            trainer_profile.schedule = request.POST.get('schedule', trainer_profile.schedule)
            trainer_profile.whatsapp_url = request.POST.get('whatsapp_url', trainer_profile.whatsapp_url)
            trainer_profile.instagram_url = request.POST.get('instagram_url', trainer_profile.instagram_url)
            trainer_profile.save()
        else:
            athlete_profile = getattr(user, 'athlete_profile', None)
            if has_role(user, 'athlete') and athlete_profile:
                athlete_profile.instagram_url = request.POST.get('instagram_url', athlete_profile.instagram_url)
                athlete_profile.experience_years = request.POST.get('experience_years', athlete_profile.experience_years)
                athlete_profile.medical_notes = request.POST.get('medical_notes', athlete_profile.medical_notes)
                athlete_profile.save()
        
        messages.success(request, 'Профиль обновлён')
        return redirect('profile')
    
    return render(request, 'users/edit_profile.html', {'user': user})
