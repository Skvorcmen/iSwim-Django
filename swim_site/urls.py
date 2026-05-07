from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import index, search
from news.views import NewsListView, NewsDetailView, toggle_like, add_comment_ajax
from academy.views import ArticleListView, ArticleDetailView
from academy.views import toggle_like as article_toggle_like, add_comment_ajax as article_add_comment
from branches.views import BranchListView, BranchDetailView, BranchCabinetView, add_comment_ajax as branch_add_comment
from trainers.views import TrainerListView, TrainerDetailView
from users.views import (
    profile_redirect, AthleteProfileView, FanProfileView, TrainerProfileView,
    WallOfFameView, PublicAthleteView, PublicFanView, edit_profile,
)
from chat.views import chat_list, chat_room, create_room, get_users, unread_count
from activity.views import ActivityListView, PersonalActivityListView
from competitions.views import (
    CompetitionListView, CompetitionDetailView, CompetitionCreateView,
    download_template_excel, upload_application, generate_heats, manage_heats,
    LiveCompetitionView, save_result, heat_data,
    available_athletes, add_to_heat, manual_register,
    PublicResultsView, CompetitionProtocolView, download_competition_protocol_csv,
    finalize_results, reorder_heats, remove_from_heat,
    group_heats_data, registered_athletes, finish_competition,
    download_import_errors_csv,
    competition_api_list, competition_api_detail,
    competition_api_results, competition_api_heat_assignments,
)

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('search/', search, name='search'),

    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
    path('news/<slug:slug>/like/', toggle_like, name='toggle_like'),
    path('news/<slug:slug>/comment/ajax/', add_comment_ajax, name='add_comment_ajax'),

    path('academy/', ArticleListView.as_view(), name='article_list'),
    path('academy/<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),
    path('academy/<slug:slug>/like/', article_toggle_like, name='article_toggle_like'),
    path('academy/<slug:slug>/comment/ajax/', article_add_comment, name='article_add_comment'),

    path('branches/', BranchListView.as_view(), name='branch_list'),
    path('branches/<int:pk>/', BranchDetailView.as_view(), name='branch_detail'),
    path('branches/<int:pk>/cabinet/', BranchCabinetView.as_view(), name='branch_cabinet'),
    path('branches/<int:pk>/comment/ajax/', branch_add_comment, name='branch_add_comment'),

    path('trainers/', TrainerListView.as_view(), name='trainer_list'),
    path('trainers/<int:pk>/', TrainerDetailView.as_view(), name='trainer_detail'),

    path('profile/', profile_redirect, name='profile'),
    path('profile/athlete/', AthleteProfileView.as_view(), name='athlete_profile'),
    path('profile/fan/', FanProfileView.as_view(), name='fan_profile'),
    path('profile/trainer/', TrainerProfileView.as_view(), name='trainer_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    path('wall-of-fame/', WallOfFameView.as_view(), name='wall_of_fame'),
    path('athlete/<str:username>/', PublicAthleteView.as_view(), name='public_athlete'),
    path('fan/<str:username>/', PublicFanView.as_view(), name='public_fan'),

    path('activity/', ActivityListView.as_view(), name='activity_list'),
    path('activity/me/', PersonalActivityListView.as_view(), name='activity_personal_list'),

    path('chat/', chat_list, name='chat_list'),
    path('chat/<int:room_id>/', chat_room, name='chat_room'),
    path('chat/create/', create_room, name='create_room'),
    path('chat/api/users/', get_users, name='chat_users_api'),
    path('chat/api/unread/', unread_count, name='unread_count'),

    path('competitions/', CompetitionListView.as_view(), name='competition_list'),
    path('competitions/create/', CompetitionCreateView.as_view(), name='competition_create'),
    path('competitions/<int:pk>/', CompetitionDetailView.as_view(), name='competition_detail'),
    path('competitions/<int:pk>/template/', download_template_excel, name='download_template_excel'),
    path('competitions/<int:pk>/upload/', upload_application, name='upload_application'),
    path('competitions/<int:pk>/heats/generate/', generate_heats, name='generate_heats'),
    path('competitions/<int:pk>/heats/', manage_heats, name='manage_heats'),
    path('competitions/<int:pk>/live/', LiveCompetitionView.as_view(), name='live_competition'),
    path('competitions/heats/<int:heat_id>/data/', heat_data, name='heat_data'),
    path('competitions/assignment/<int:assignment_id>/save/', save_result, name='save_result'),

    path('competitions/heats/<int:heat_id>/available/', available_athletes, name='available_athletes'),
    path('competitions/heats/<int:heat_id>/add/', add_to_heat, name='add_to_heat'),
    path('competitions/<int:pk>/manual-register/', manual_register, name='manual_register'),
    path('competitions/<int:pk>/results/', PublicResultsView.as_view(), name='public_results'),
    path('competitions/<int:pk>/protocol/', CompetitionProtocolView.as_view(), name='competition_protocol'),
    path('competitions/<int:pk>/protocol.csv', download_competition_protocol_csv, name='competition_protocol_csv'),
    path('competitions/<int:pk>/finalize/<int:discipline_id>/<int:category_id>/', finalize_results, name='finalize_results'),
    path('competitions/<int:pk>/heats/reorder/', reorder_heats, name='reorder_heats'),
    path('competitions/assignment/<int:assignment_id>/remove/', remove_from_heat, name='remove_from_heat'),
    path('competitions/<int:pk>/heats/data/', group_heats_data, name='group_heats_data'),
    path('competitions/<int:pk>/registered/', registered_athletes, name='registered_athletes'),
    path('competitions/<int:pk>/finish/', finish_competition, name='finish_competition'),
    path('competitions/<int:pk>/upload/errors.csv', download_import_errors_csv, name='download_import_errors_csv'),

    path('competitions/api/', competition_api_list, name='competition_api_list'),
    path('competitions/api/<int:pk>/', competition_api_detail, name='competition_api_detail'),
    path('competitions/api/<int:pk>/results/', competition_api_results, name='competition_api_results'),
    path('competitions/api/heats/<int:heat_id>/', competition_api_heat_assignments, name='competition_api_heat_assignments'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
