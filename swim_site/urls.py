from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home(request):
    return HttpResponse('Django is working! Now adding features step by step.')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
]
