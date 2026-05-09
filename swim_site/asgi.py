import os
import sys
from django.core.asgi import get_asgi_application

# Принудительно устанавливаем настройки
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swim_site.settings')

# DEBUG: проверяем, что настройки загружаются
try:
    from django.conf import settings
    print(f"DEBUG: ROOT_URLCONF = {getattr(settings, 'ROOT_URLCONF', 'NOT SET')}", file=sys.stderr)
except Exception as e:
    print(f"DEBUG: Error loading settings: {e}", file=sys.stderr)

application = get_asgi_application()
print("DEBUG: ASGI application created successfully", file=sys.stderr)
