"""
TTS Service for Interpretation App

Provides text-to-speech synthesis using DashScope Qwen TTS models.
"""

import asyncio
import logging
import os
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TTSConfig:
    """TTS configuration"""
    voice: str = "Cherry"
    language: str = "Auto"
    model: str = "qwen3-tts-flash"


class TTSService:
    """
    TTS Service for synthesizing translated text to speech.
    
    Uses DashScope Qwen TTS for high-quality Chinese/English synthesis.
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._provider = None
    
    def _get_provider(self):
        """Lazy-load TTS provider"""
        if self._provider is None:
            from common.providers import ProviderManager, ServiceType
            from common.providers.base import ProviderConfig, ProviderType
            
            config = ProviderConfig(
                provider_type=ProviderType.DASHSCOPE,
                api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
                model=self.config.model,
                extra_params={"voice": self.config.voice}
            )
            
            self._provider = ProviderManager.get_provider(
                ServiceType.TTS,
                provider_type=ProviderType.DASHSCOPE,
                model=self.config.model,
                voice=self.config.voice,
            )
        return self._provider
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """
        Synthesize text to speech asynchronously.
        
        Args:
            text: Text to synthesize
            voice: Voice ID (optional, uses default from config)
            language: Language hint (optional)
            
        Returns:
            Dict with audio_url and metadata
        """
        if not text or not text.strip():
            return {"success": False, "error": "Empty text"}
        
        # Truncate if too long (qwen3-tts-flash limit is 600 chars)
        max_chars = 600
        if len(text) > max_chars:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars}")
            text = text[:max_chars]
        
        try:
            provider = self._get_provider()
            
            response = await provider.synthesize_async(
                text=text,
                voice=voice or self.config.voice,
                language=language or self.config.language,
            )
            
            return {
                "success": True,
                "audio_url": response.audio_url,
                "characters": response.characters,
                "expires_at": response.expires_at,
                "request_id": response.request_id,
            }
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def synthesize_sync(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
    ) -> dict:
        """
        Synchronous wrapper for synthesize.
        """
        return asyncio.run(self.synthesize(text, voice, language))
    
    @staticmethod
    def get_available_voices() -> dict:
        """Get available voice options"""
        from common.providers.dashscope_tts import QWEN_TTS_VOICES
        return QWEN_TTS_VOICES
    
    @staticmethod
    def get_voice_for_language(target_lang: str) -> str:
        """
        Get a recommended voice for the target language.
        
        Returns appropriate voice based on target language.
        """
        # For Chinese targets, use Cherry (warm female voice)
        # For English targets, use Vivian (professional female voice)
        chinese_langs = ["Chinese", "中文", "zh", "cn"]
        english_langs = ["English", "英文", "en"]
        
        if any(lang in target_lang for lang in chinese_langs):
            return "Cherry"
        elif any(lang in target_lang for lang in english_langs):
            return "Vivian"
        else:
            return "Cherry"  # Default
