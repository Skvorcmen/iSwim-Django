from django.urls import path
from .consumers import CompetitionLiveConsumer


websocket_urlpatterns = [
    path("ws/competitions/<int:competition_id>/", CompetitionLiveConsumer.as_asgi()),
]
