from django.urls import path
from . import views

app_name = 'athlete_stats'

urlpatterns = [
    path('', views.AthleteStatsView.as_view(), name='my_stats'),
    path('<str:username>/', views.AthleteStatsView.as_view(), name='athlete_stats'),
    path('progress/<int:athlete_id>/<int:discipline_id>/', views.progress_data, name='progress_data'),
]
