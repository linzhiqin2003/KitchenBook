"""
Provider Registry and Factory

Central registry for managing AI providers and creating them on demand.
"""

import os
import logging
from typing import Dict, Optional, Type, Any

from .base import (
    BaseProvider,
    ProviderConfig,
    ProviderType,
    ServiceType,
    LLMProvider,
    ASRProvider,
    TTSProvider,
    TranslationProvider,
)
from .dashscope import DashScopeLLMProvider, DashScopeTranslationProvider
from .dashscope_tts import DashScopeTTSProvider
from .openai_provider import OpenAILLMProvider, OpenAITTSProvider

logger = logging.getLogger(__name__)


# Registry mapping (provider_type, service_type) -> provider_class
PROVIDER_REGISTRY: Dict[tuple, Type[BaseProvider]] = {
    # DashScope providers
    (ProviderType.DASHSCOPE, ServiceType.LLM): DashScopeLLMProvider,
    (ProviderType.DASHSCOPE, ServiceType.TRANSLATION): DashScopeTranslationProvider,
    (ProviderType.DASHSCOPE, ServiceType.TTS): DashScopeTTSProvider,
    
    # OpenAI providers
    (ProviderType.OPENAI, ServiceType.LLM): OpenAILLMProvider,
    (ProviderType.OPENAI, ServiceType.VISION): OpenAILLMProvider,
    (ProviderType.OPENAI, ServiceType.TTS): OpenAITTSProvider,
}


# Default provider for each service type
DEFAULT_PROVIDERS: Dict[ServiceType, ProviderType] = {
    ServiceType.LLM: ProviderType.DASHSCOPE,
    ServiceType.ASR: ProviderType.DASHSCOPE,
    ServiceType.TTS: ProviderType.DASHSCOPE,  # Changed to DashScope for Qwen TTS
    ServiceType.TRANSLATION: ProviderType.DASHSCOPE,
    ServiceType.VISION: ProviderType.OPENAI,
}


# API key environment variable names for each provider
API_KEY_ENV_VARS: Dict[ProviderType, str] = {
    ProviderType.DASHSCOPE: "DASHSCOPE_API_KEY",
    ProviderType.OPENAI: "OPENAI_API_KEY",
    ProviderType.AZURE: "AZURE_OPENAI_API_KEY",
    ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
    ProviderType.GOOGLE: "GOOGLE_API_KEY",
}


class ProviderManager:
    """
    Central manager for AI providers.
    
    Handles provider registration, creation, and caching.
    """
    
    _instance = None
    _providers: Dict[str, BaseProvider] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {}
        return cls._instance
    
    @classmethod
    def get_provider(
        cls,
        service_type: ServiceType,
        provider_type: Optional[ProviderType] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        cache: bool = True,
        **kwargs
    ) -> BaseProvider:
        """
        Get or create a provider for the specified service.
        
        Args:
            service_type: Type of service needed (LLM, ASR, TTS, etc.)
            provider_type: Optional specific provider to use
            model: Optional model override
            api_key: Optional API key (otherwise from env)
            cache: Whether to cache and reuse the provider instance
            **kwargs: Additional provider configuration
            
        Returns:
            Configured provider instance
        """
        instance = cls()
        
        # Use default provider if not specified
        if provider_type is None:
            provider_type = DEFAULT_PROVIDERS.get(service_type)
            if provider_type is None:
                raise ValueError(f"No default provider for service type: {service_type}")
        
        # Generate cache key
        cache_key = f"{provider_type.value}:{service_type.value}:{model or 'default'}"
        
        # Check cache
        if cache and cache_key in instance._providers:
            return instance._providers[cache_key]
        
        # Get API key
        if api_key is None:
            env_var = API_KEY_ENV_VARS.get(provider_type)
            if env_var:
                api_key = os.environ.get(env_var)
            if not api_key:
                raise ValueError(
                    f"API key not provided and {env_var} environment variable not set"
                )
        
        # Get provider class
        provider_cls = PROVIDER_REGISTRY.get((provider_type, service_type))
        if provider_cls is None:
            raise ValueError(
                f"No provider registered for {provider_type.value} + {service_type.value}"
            )
        
        # Create config
        config = ProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            model=model,
            extra_params=kwargs,
        )
        
        # Create provider
        provider = provider_cls(config)
        
        # Cache if requested
        if cache:
            instance._providers[cache_key] = provider
        
        return provider
    
    @classmethod
    def get_llm(
        cls,
        provider_type: Optional[ProviderType] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """Convenience method to get an LLM provider"""
        return cls.get_provider(ServiceType.LLM, provider_type, model, **kwargs)
    
    @classmethod
    def get_translation(
        cls,
        provider_type: Optional[ProviderType] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TranslationProvider:
        """Convenience method to get a translation provider"""
        return cls.get_provider(ServiceType.TRANSLATION, provider_type, model, **kwargs)
    
    @classmethod
    def get_tts(
        cls,
        provider_type: Optional[ProviderType] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TTSProvider:
        """Convenience method to get a TTS provider"""
        return cls.get_provider(ServiceType.TTS, provider_type, model, **kwargs)
    
    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        service_type: ServiceType,
        provider_class: Type[BaseProvider]
    ):
        """
        Register a new provider class.
        
        Use this to add custom providers or override existing ones.
        """
        PROVIDER_REGISTRY[(provider_type, service_type)] = provider_class
        logger.info(f"Registered provider: {provider_type.value} + {service_type.value}")
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached provider instances"""
        instance = cls()
        instance._providers.clear()
    
    @classmethod
    def list_available(cls) -> Dict[str, list]:
        """List all available providers and their supported services"""
        result = {}
        for (provider_type, service_type), _ in PROVIDER_REGISTRY.items():
            key = provider_type.value
            if key not in result:
                result[key] = []
            result[key].append(service_type.value)
        return result


# Convenience functions for quick access
def get_llm(
    provider: str = "dashscope",
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """Quick access to LLM provider"""
    provider_type = ProviderType(provider)
    return ProviderManager.get_llm(provider_type, model, **kwargs)


def get_translation(
    provider: str = "dashscope",
    model: Optional[str] = None,
    **kwargs
) -> TranslationProvider:
    """Quick access to translation provider"""
    provider_type = ProviderType(provider)
    return ProviderManager.get_translation(provider_type, model, **kwargs)


def get_tts(
    provider: str = "openai",
    model: Optional[str] = None,
    **kwargs
) -> TTSProvider:
    """Quick access to TTS provider"""
    provider_type = ProviderType(provider)
    return ProviderManager.get_tts(provider_type, model, **kwargs)
