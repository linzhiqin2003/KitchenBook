"""
WebSocket URL routing for games.
"""

from django.urls import path

from .consumers import GomokuConsumer

websocket_urlpatterns = [
    path("ws/games/gomoku/<str:room_id>/", GomokuConsumer.as_asgi()),
]

