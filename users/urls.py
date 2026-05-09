from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.WallOfFameView.as_view(), name='wall_of_fame'),
]
