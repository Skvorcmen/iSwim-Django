from django.views.generic import ListView, DetailView
from .models import Trainer

class TrainerListView(ListView):
    model = Trainer
    template_name = 'trainers/trainer_list.html'
    context_object_name = 'trainers'

class TrainerDetailView(DetailView):
    model = Trainer
    template_name = 'trainers/trainer_detail.html'
    context_object_name = 'trainer'
