from django.urls import path
from . import views

app_name = 'branches'

urlpatterns = [
    path('', views.BranchListView.as_view(), name='branch_list'),
    path('<int:pk>/', views.BranchDetailView.as_view(), name='branch_detail'),
]
