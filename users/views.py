from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Count
from .models import AthleteProfile, FanProfile, Achievement
from trainers.models import Trainer

@login_required
def profile_redirect(request):
    user = request.user
    if user.is_staff or user.is_superuser:
        return render(request, 'users/admin_profile.html')
    if hasattr(user, 'trainer_profile'):
        return redirect('trainer_profile')
    elif hasattr(user, 'athlete_profile'):
        return redirect('athlete_profile')
    elif hasattr(user, 'fan_profile'):
        return redirect('fan_profile')
    else:
        return render(request, 'users/profile_choice.html')

class AthleteProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/athlete_profile.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile'] = self.request.user.athlete_profile
        return ctx

class FanProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/fan_profile.html'

class TrainerProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/trainer_profile.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['trainer'] = self.request.user.trainer_profile
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
        ctx['achievements'] = self.object.achievements.all()
        return ctx
from django.contrib import messages

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
        
        if hasattr(user, 'trainer_profile'):
            tp = user.trainer_profile
            tp.bio = request.POST.get('bio', tp.bio)
            tp.specialization = request.POST.get('specialization', tp.specialization)
            tp.save()
        elif hasattr(user, 'athlete_profile'):
            ap = user.athlete_profile
            ap.medical_notes = request.POST.get('medical_notes', ap.medical_notes)
            ap.save()
        
        messages.success(request, 'Профиль обновлён')
        return redirect('profile')
    
    return render(request, 'users/edit_profile.html', {'user': user})
