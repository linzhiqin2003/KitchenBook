"""
API URL configuration
"""

from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.get_config, name='get_config'),
    path('languages/', views.get_languages, name='get_languages'),
    path('translate/', views.translate_text, name='translate_text'),
    path('health/', views.health_check, name='health_check'),
    path('tts-voices/', views.get_tts_voices, name='get_tts_voices'),
    path('submit-file-asr/', views.submit_file_asr, name='submit_file_asr'),
    path('submit-file-translation/', views.submit_file_translation, name='submit_file_translation'),
    path('get-asr-result/', views.get_asr_result, name='get_asr_result'),
]
