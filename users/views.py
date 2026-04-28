from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .models import AthleteProfile, FanProfile
from trainers.models import Trainer

@login_required
def profile_redirect(request):
    user = request.user
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
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.athlete_profile
        return context

class FanProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/fan_profile.html'

class TrainerProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/trainer_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trainer'] = self.request.user.trainer_profile
        return context
