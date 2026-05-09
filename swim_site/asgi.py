import os
import sys
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swim_site.settings')

print("DEBUG: asgi.py loading, about to get application", file=sys.stderr)

try:
    application = get_asgi_application()
    print("DEBUG: ASGI application created successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG: Error creating ASGI application: {e}", file=sys.stderr)
    raise

# Проверяем URLconf после создания приложения
from django.urls import get_resolver
print(f"DEBUG: URL patterns loaded: {get_resolver().url_patterns}", file=sys.stderr)
