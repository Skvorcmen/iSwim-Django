from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import index
from news.views import NewsListView, NewsDetailView, toggle_like, add_comment_ajax
from academy.views import ArticleListView, ArticleDetailView
from branches.views import BranchListView, BranchDetailView
from trainers.views import TrainerListView, TrainerDetailView
from users.views import profile_redirect, AthleteProfileView, FanProfileView, TrainerProfileView

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
    path('news/<slug:slug>/like/', toggle_like, name='toggle_like'),
    path('news/<slug:slug>/comment/ajax/', add_comment_ajax, name='add_comment_ajax'),
    path('academy/', ArticleListView.as_view(), name='article_list'),
    path('academy/<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),
    path('branches/', BranchListView.as_view(), name='branch_list'),
    path('branches/<int:pk>/', BranchDetailView.as_view(), name='branch_detail'),
    path('trainers/', TrainerListView.as_view(), name='trainer_list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer_detail'),
    path('profile/', profile_redirect, name='profile'),
    path('profile/athlete/', AthleteProfileView.as_view(), name='athlete_profile'),
    path('profile/fan/', FanProfileView.as_view(), name='fan_profile'),
    path('profile/trainer/', TrainerProfileView.as_view(), name='trainer_profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from academy.views import toggle_like as article_toggle_like, add_comment_ajax as article_add_comment

urlpatterns += [
    path('academy/<slug:slug>/like/', article_toggle_like, name='article_toggle_like'),
    path('academy/<slug:slug>/comment/ajax/', article_add_comment, name='article_add_comment'),
]
