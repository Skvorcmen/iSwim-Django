from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home(request):
    return HttpResponse("""
    <h2>✅ Все приложения загружены!</h2>
    <ul>
        <li><a href="/admin/">Admin</a></li>
        <li><a href="/accounts/login/">Login</a></li>
        <li><a href="/stats/">My Stats</a></li>
        <li><a href="/competitions/">Competitions</a></li>
        <li><a href="/news/">News</a></li>
        <li><a href="/academy/">Academy</a></li>
        <li><a href="/branches/">Branches</a></li>
        <li><a href="/trainers/">Trainers</a></li>
        <li><a href="/chat/">Chat</a></li>
        <li><a href="/activity/">Activity</a></li>
        <li><a href="/wall-of-fame/">Wall of Fame</a></li>
    </ul>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('stats/', include('athlete_stats.urls')),
    path('competitions/', include('competitions.urls')),
    path('news/', include('news.urls')),
    path('academy/', include('academy.urls')),
    path('branches/', include('branches.urls')),
    path('trainers/', include('trainers.urls')),
    path('chat/', include('chat.urls')),
    path('activity/', include('activity.urls')),
    path('wall-of-fame/', include('users.urls')),
    path('', home),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
