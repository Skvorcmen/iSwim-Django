import sys
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

print("DEBUG: urls.py is loading!", file=sys.stderr)

def health_check(request):
    print("DEBUG: health_check view called!", file=sys.stderr)
    return HttpResponse('OK')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('health/', health_check, name='health_check'),
]

print(f"DEBUG: urlpatterns = {[p.pattern.regex.pattern for p in urlpatterns if hasattr(p, 'pattern')]}", file=sys.stderr)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
