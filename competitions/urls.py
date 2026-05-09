from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    path('', views.CompetitionListView.as_view(), name='competition_list'),
    path('<int:pk>/', views.CompetitionDetailView.as_view(), name='competition_detail'),
    path('<int:pk>/results/', views.PublicResultsView.as_view(), name='public_results'),
    path('<int:pk>/live/', views.LiveCompetitionView.as_view(), name='live_competition'),
]
