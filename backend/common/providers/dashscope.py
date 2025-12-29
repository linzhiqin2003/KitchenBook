"""
DashScope (Aliyun) Provider Implementation

Supports:
- LLM (Qwen series)
- ASR (Qwen-ASR-Realtime)
- TTS (CosyVoice)
- Translation (Qwen-MT)
"""

import asyncio
import base64
import logging
import queue
import threading
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import OpenAI, AsyncOpenAI

from .base import (
    ProviderConfig,
    ProviderType,
    ServiceType,
    Message,
    LLMResponse,
    ASRResult,
    TranslationResult,
    LLMProvider,
    TranslationProvider,
)

logger = logging.getLogger(__name__)


class DashScopeLLMProvider(LLMProvider):
    """
    DashScope LLM Provider using OpenAI-compatible API
    
    Supports Qwen series models via DashScope's OpenAI-compatible endpoint.
    """
    
    # Default models for different tasks
    DEFAULT_MODELS = {
        "chat": "qwen-plus",
        "long_context": "qwen-long",
        "fast": "qwen-turbo",
        "code": "qwen-coder-plus",
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Initialize OpenAI-compatible clients
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.async_client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.default_model = config.model or self.DEFAULT_MODELS["chat"]
    
    def get_supported_services(self) -> List[ServiceType]:
        return [ServiceType.LLM]
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """Convert Message objects to OpenAI format"""
        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
    
    def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Synchronous chat completion"""
        try:
            completion = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=self._convert_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            choice = completion.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                role=choice.message.role,
                finish_reason=choice.finish_reason,
                usage=dict(completion.usage) if completion.usage else None,
                raw_response=completion,
            )
        except Exception as e:
            logger.error(f"DashScope chat error: {e}")
            raise
    
    async def chat_async(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Asynchronous chat completion"""
        try:
            completion = await self.async_client.chat.completions.create(
                model=model or self.default_model,
                messages=self._convert_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            choice = completion.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                role=choice.message.role,
                finish_reason=choice.finish_reason,
                usage=dict(completion.usage) if completion.usage else None,
                raw_response=completion,
            )
        except Exception as e:
            logger.error(f"DashScope async chat error: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Streaming chat completion"""
        try:
            stream = await self.async_client.chat.completions.create(
                model=model or self.default_model,
                messages=self._convert_messages(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"DashScope stream chat error: {e}")
            raise


class DashScopeTranslationProvider(TranslationProvider):
    """
    DashScope Translation Provider using Qwen-MT models
    
    Uses OpenAI-compatible API with translation_options.
    """
    
    DEFAULT_MODELS = {
        "default": "qwen-mt-turbo",
        "high_quality": "qwen-mt-plus",
        "fast": "qwen-mt-turbo",
        "streaming": "qwen-mt-flash",
        "lite": "qwen-mt-lite",
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.async_client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.default_model = config.model or self.DEFAULT_MODELS["default"]
    
    def get_supported_services(self) -> List[ServiceType]:
        return [ServiceType.TRANSLATION]
    
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "English",
        model: Optional[str] = None,
        temperature: float = 0.65,
        **kwargs
    ) -> TranslationResult:
        """Synchronous translation"""
        try:
            completion = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[{"role": "user", "content": text}],
                extra_body={
                    "translation_options": {
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                    }
                },
                temperature=temperature,
                **kwargs
            )
            
            translated = completion.choices[0].message.content
            
            return TranslationResult(
                original_text=text,
                translated_text=translated or "",
                source_lang=source_lang,
                target_lang=target_lang,
            )
        except Exception as e:
            logger.error(f"DashScope translation error: {e}")
            raise
    
    async def translate_async(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "English",
        model: Optional[str] = None,
        temperature: float = 0.65,
        **kwargs
    ) -> TranslationResult:
        """Asynchronous translation"""
        try:
            completion = await self.async_client.chat.completions.create(
                model=model or self.default_model,
                messages=[{"role": "user", "content": text}],
                extra_body={
                    "translation_options": {
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                    }
                },
                temperature=temperature,
                **kwargs
            )
            
            translated = completion.choices[0].message.content
            
            return TranslationResult(
                original_text=text,
                translated_text=translated or "",
                source_lang=source_lang,
                target_lang=target_lang,
            )
        except Exception as e:
            logger.error(f"DashScope async translation error: {e}")
            raise
    
    async def translate_stream(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "English",
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Streaming translation"""
        try:
            stream = await self.async_client.chat.completions.create(
                model=model or "qwen-mt-flash",  # Flash model supports streaming
                messages=[{"role": "user", "content": text}],
                extra_body={
                    "translation_options": {
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                    }
                },
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"DashScope stream translation error: {e}")
            raise


# Factory function to create DashScope providers
def create_dashscope_provider(
    api_key: str,
    service_type: ServiceType,
    model: Optional[str] = None,
    **kwargs
):
    """
    Factory function to create appropriate DashScope provider
    
    Args:
        api_key: DashScope API key
        service_type: Type of service needed
        model: Optional model override
        **kwargs: Additional provider configuration
        
    Returns:
        Appropriate provider instance
    """
    config = ProviderConfig(
        provider_type=ProviderType.DASHSCOPE,
        api_key=api_key,
        model=model,
        **kwargs
    )
    
    providers = {
        ServiceType.LLM: DashScopeLLMProvider,
        ServiceType.TRANSLATION: DashScopeTranslationProvider,
    }
    
    provider_class = providers.get(service_type)
    if not provider_class:
        raise ValueError(f"DashScope does not support service type: {service_type}")
    
    return provider_class(config)
