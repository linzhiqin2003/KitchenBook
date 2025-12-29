"""
Emoji Generator App Configuration
"""

from django.apps import AppConfig


class EmojiGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emoji_generator'
    label = 'emoji_generator'
    verbose_name = 'Emoji Generator'
