"""
Translation Service using AI providers

Supports multiple translation providers through the unified provider interface.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from common.config import get_settings
from common.providers import ProviderManager, ServiceType, ProviderType

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Represents a translation result"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str


class TranslationService:
    """
    Translation Service using configurable AI providers.
    
    Default uses DashScope Qwen-MT, but can be configured to use other providers.
    """

    def __init__(
        self,
        target_lang: str = "Chinese",
        source_lang: str = "auto",
        provider: str = "dashscope",
        model: Optional[str] = None,
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Get the translation provider
        settings = get_settings()
        self.model = model or settings.translation.model
        
        # Create provider
        provider_type = ProviderType(provider)
        self._provider = ProviderManager.get_provider(
            ServiceType.TRANSLATION,
            provider_type,
            model=self.model,
        )

    def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> TranslationResult:
        """
        Synchronous translation
        """
        source = source_lang or self.source_lang
        target = target_lang or self.target_lang
        
        try:
            result = self._provider.translate(
                text,
                source_lang=source,
                target_lang=target,
            )
            
            return TranslationResult(
                original_text=result.original_text,
                translated_text=result.translated_text,
                source_lang=result.source_lang,
                target_lang=result.target_lang,
            )
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise

    async def translate_async(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> TranslationResult:
        """
        Asynchronous translation
        """
        source = source_lang or self.source_lang
        target = target_lang or self.target_lang
        
        try:
            result = await self._provider.translate_async(
                text,
                source_lang=source,
                target_lang=target,
            )
            
            return TranslationResult(
                original_text=result.original_text,
                translated_text=result.translated_text,
                source_lang=result.source_lang,
                target_lang=result.target_lang,
            )
        except Exception as e:
            logger.error(f"Async translation error: {e}")
            raise


# Convenience functions
async def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "Chinese",
) -> str:
    """Quick translation function"""
    service = TranslationService(target_lang=target_lang, source_lang=source_lang)
    result = await service.translate_async(text, source_lang, target_lang)
    return result.translated_text
