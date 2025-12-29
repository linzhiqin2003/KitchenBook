"""
OpenAI Provider Implementation

Supports:
- LLM (GPT-5, o3, o4-mini, etc.)
- TTS (tts-1, tts-1-hd, gpt-5-audio)
- ASR (Whisper v3, gpt-5-audio)
- Embedding
- Vision (GPT-5, o3-vision)
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import OpenAI, AsyncOpenAI

from .base import (
    ProviderConfig,
    ProviderType,
    ServiceType,
    Message,
    LLMResponse,
    ASRResult,
    TTSResult,
    LLMProvider,
    ASRProvider,
    TTSProvider,
)

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI LLM Provider
    
    Supports GPT-5.2, o3, o4-mini, and other latest OpenAI models.
    GPT-4 series is considered legacy.
    """
    
    DEFAULT_MODELS = {
        "chat": "gpt-5",            # Standard Driver
        "advanced": "gpt-5.2",      # Late 2025 SOTA
        "reasoning": "o3",          # Advanced Reasoning
        "fast": "o4-mini",          # High intelligence, low latency
        "legacy": "gpt-4o",         # Legacy
    }
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.async_client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.default_model = config.model or self.DEFAULT_MODELS["chat"]
    
    def get_supported_services(self) -> List[ServiceType]:
        return [ServiceType.LLM, ServiceType.VISION]
    
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
            logger.error(f"OpenAI chat error: {e}")
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
            logger.error(f"OpenAI async chat error: {e}")
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
            logger.error(f"OpenAI stream chat error: {e}")
            raise


class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS Provider
    
    Supports tts-1 and tts-1-hd models.
    """
    
    DEFAULT_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.async_client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.default_model = config.model or "tts-1"
        self.default_voice = config.extra_params.get("voice", "alloy")
    
    def get_supported_services(self) -> List[ServiceType]:
        return [ServiceType.TTS]
    
    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        response_format: str = "mp3",
        **kwargs
    ) -> TTSResult:
        """Synthesize text to speech"""
        try:
            response = self.client.audio.speech.create(
                model=model or self.default_model,
                voice=voice or self.default_voice,
                input=text,
                response_format=response_format,
                **kwargs
            )
            
            return TTSResult(
                audio_data=response.content,
                format=response_format,
                sample_rate=24000 if response_format == "mp3" else 16000,
            )
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            raise
    
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Streaming TTS (OpenAI doesn't natively support, but we can chunk)"""
        # OpenAI TTS doesn't support true streaming, so we just yield the full audio
        result = self.synthesize(text, voice, model, **kwargs)
        yield result.audio_data


# Factory function
def create_openai_provider(
    api_key: str,
    service_type: ServiceType,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs
):
    """
    Factory function to create appropriate OpenAI provider
    """
    config = ProviderConfig(
        provider_type=ProviderType.OPENAI,
        api_key=api_key,
        base_url=base_url,
        model=model,
        extra_params=kwargs,
    )
    
    providers = {
        ServiceType.LLM: OpenAILLMProvider,
        ServiceType.VISION: OpenAILLMProvider,  # GPT-4V uses same interface
        ServiceType.TTS: OpenAITTSProvider,
    }
    
    provider_class = providers.get(service_type)
    if not provider_class:
        raise ValueError(f"OpenAI provider does not support service type: {service_type}")
    
    return provider_class(config)
