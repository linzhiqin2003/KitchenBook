"""
Common utilities and base classes for AI Service Platform

This package provides:
- providers: Unified AI provider interfaces (LLM, ASR, TTS, Translation)
- config: Centralized configuration management
- models: Common data models
- utils: Utility functions
"""

from .config import (
    get_settings,
    reload_settings,
    AppSettings,
    APIConfig,
    ASRConfig,
    TranslationConfig,
    LLMConfig,
    SUPPORTED_LANGUAGES,
    get_language_name,
)

from .providers import (
    ProviderManager,
    ProviderType,
    ServiceType,
    get_llm,
    get_translation,
    get_tts,
)

__all__ = [
    # Config
    "get_settings",
    "reload_settings",
    "AppSettings",
    "APIConfig",
    "ASRConfig",
    "TranslationConfig",
    "LLMConfig",
    "SUPPORTED_LANGUAGES",
    "get_language_name",
    
    # Providers
    "ProviderManager",
    "ProviderType",
    "ServiceType",
    "get_llm",
    "get_translation",
    "get_tts",
]
