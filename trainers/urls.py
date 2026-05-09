from django.urls import path
from . import views

app_name = 'trainers'

urlpatterns = [
    path('', views.TrainerListView.as_view(), name='trainer_list'),
    path('<int:pk>/', views.TrainerDetailView.as_view(), name='trainer_detail'),
]
