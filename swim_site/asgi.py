import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'swim_site.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from competitions.routing import websocket_urlpatterns as competition_websocket_urlpatterns

websocket_urlpatterns = chat_websocket_urlpatterns + competition_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
