"""
Interpretation App Configuration
"""

from django.apps import AppConfig


class InterpretationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.interpretation'
    label = 'interpretation'
    verbose_name = 'Real-time Interpretation'
