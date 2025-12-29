"""
WebSocket URL routing for Interpretation App
"""

from django.urls import path
from .consumers import ASRConsumer

websocket_urlpatterns = [
    path('ws/interpretation/', ASRConsumer.as_asgi()),
    # Keep legacy route for backward compatibility
    path('ws/asr/', ASRConsumer.as_asgi()),
]
