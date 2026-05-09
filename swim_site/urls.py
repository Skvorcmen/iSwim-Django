from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    user_status = "Вы вошли как " + request.user.username if request.user.is_authenticated else "Вы не вошли"
    login_link = '<a href="/accounts/login/">Войти</a>'
    logout_link = '<a href="/accounts/logout/">Выйти</a>' if request.user.is_authenticated else ''
    return HttpResponse(f"✅ Django + allauth работают! {user_status}<br>{login_link} | {logout_link}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', home),
]
