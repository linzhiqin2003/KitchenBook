"""
DashScope TTS Provider

Implements TTS using Alibaba's Qwen TTS models (qwen3-tts-flash, cosyvoice series).
"""

import os
import logging
import asyncio
from typing import AsyncIterator, List, Optional

import dashscope
from dashscope import MultiModalConversation

from .base import (
    TTSProvider,
    TTSResult,
    ProviderConfig,
    ServiceType,
)

logger = logging.getLogger(__name__)

# Available voices for Qwen TTS (qwen3-tts-flash)
# Full list from official documentation: https://help.aliyun.com/zh/model-studio/
QWEN_TTS_VOICES = {
    # Standard voices
    "Cherry": {"gender": "female", "style": "warm", "description": "芊悦 - 阳光积极、亲切自然的女声", "emoji": "🌸"},
    "Ethan": {"gender": "male", "style": "warm", "description": "晨煦 - 阳光、温暖、活力的男声", "emoji": "☀️"},
    "Nofish": {"gender": "male", "style": "designer", "description": "不吃鱼 - 不会翘舌音的设计师", "emoji": "🐟"},
    "Jennifer": {"gender": "female", "style": "professional", "description": "詹妮弗 - 品牌级电影质感美语女声", "emoji": "🎬"},
    "Ryan": {"gender": "male", "style": "dramatic", "description": "甜茶 - 节奏感强、戏感炸裂", "emoji": "🎭"},
    "Katerina": {"gender": "female", "style": "mature", "description": "卡捷琳娜 - 御姐音、韵律回味十足", "emoji": "👑"},
    "Elias": {"gender": "male", "style": "lecturer", "description": "墨讲师 - 知识讲解、学术严谨", "emoji": "📚"},
    
    # Regional/Dialect voices
    "Jada": {"gender": "female", "style": "shanghai", "description": "上海阿珍 - 风风火火的沪上阿姐", "emoji": "🏙️"},
    "Dylan": {"gender": "male", "style": "beijing", "description": "北京晓东 - 北京胡同少年", "emoji": "🏯"},
    "Sunny": {"gender": "female", "style": "sichuan", "description": "四川晴儿 - 甜美可爱的川妹子", "emoji": "🌶️"},
    "Li": {"gender": "male", "style": "nanjing", "description": "南京老李 - 耐心的瑜伽老师", "emoji": "🧘"},
    "Marcus": {"gender": "male", "style": "shaanxi", "description": "陕西秦川 - 富有老陕味道", "emoji": "⛰️"},
    "Roy": {"gender": "male", "style": "minnan", "description": "闽南阿杰 - 诙谐直爽、市井活泼", "emoji": "🍵"},
}

# Language mapping
LANGUAGE_MAPPING = {
    "Chinese": "Chinese",
    "zh": "Chinese",
    "cn": "Chinese",
    "中文": "Chinese",
    "English": "English",
    "en": "English",
    "英文": "English",
    "Japanese": "Japanese",
    "jp": "Japanese",
    "ja": "Japanese",
    "日语": "Japanese",
    "Korean": "Korean",
    "ko": "Korean",
    "韩语": "Korean",
    "French": "French",
    "fr": "French",
    "法语": "French",
    "German": "German",
    "de": "German",
    "德语": "German",
    "Spanish": "Spanish",
    "es": "Spanish",
    "西班牙语": "Spanish",
    "Portuguese": "Portuguese",
    "pt": "Portuguese",
    "葡萄牙语": "Portuguese",
    "Italian": "Italian",
    "it": "Italian",
    "意大利语": "Italian",
    "Russian": "Russian",
    "ru": "Russian",
    "俄语": "Russian",
    "Auto": "Auto",
    "auto": "Auto",
}


class TTSResponse:
    """Response wrapper for TTS API"""
    def __init__(self, audio_url: str = None, audio_data: bytes = None, 
                 characters: int = 0, expires_at: int = None, request_id: str = None):
        self.audio_url = audio_url
        self.audio_data = audio_data
        self.characters = characters
        self.expires_at = expires_at
        self.request_id = request_id


class DashScopeTTSProvider(TTSProvider):
    """
    DashScope TTS Provider using Qwen TTS models.
    
    Supports:
    - qwen3-tts-flash (recommended, faster, up to 600 chars)
    - cosyvoice-v2 (higher quality)
    """
    
    DEFAULT_MODEL = "qwen3-tts-flash"
    DEFAULT_VOICE = "Cherry"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # Set DashScope API key
        self.api_key = config.api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required")
        
        # Set base URL for DashScope
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
        
        self.model = config.model or self.DEFAULT_MODEL
        self.voice = config.extra_params.get("voice", self.DEFAULT_VOICE)
    
    def get_supported_services(self) -> List[ServiceType]:
        return [ServiceType.TTS]
    
    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """
        Synthesize text to speech (synchronous).
        
        Args:
            text: Text to synthesize (max 600 chars for qwen3-tts-flash)
            voice: Voice ID (default: Cherry)
            language: Language hint (default: Auto)
            model: Model to use (default: qwen3-tts-flash)
            
        Returns:
            TTSResult with audio_data (bytes) containing the synthesized audio
        """
        voice = voice or self.voice
        language = LANGUAGE_MAPPING.get(language, "Auto") if language else "Auto"
        model = model or self.model
        
        try:
            response = MultiModalConversation.call(
                model=model,
                api_key=self.api_key,
                text=text,
                voice=voice,
                language_type=language,
            )
            
            if response.status_code != 200:
                raise Exception(f"TTS API error: {response.code} - {response.message}")
            
            # Get audio URL from response
            audio_url = response.output.audio.get("url", "")
            
            if not audio_url:
                raise Exception("No audio URL in response")
            
            # For synchronous call, we return a TTSResult with empty audio_data
            # but include the URL in format field for the caller to download
            return TTSResult(
                audio_data=b"",  # Empty, use the URL instead
                format=audio_url,  # Store URL in format field
                sample_rate=16000,
            )
            
        except Exception as e:
            self.logger.error(f"TTS synthesis error: {e}")
            raise
    
    async def synthesize_async(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> TTSResponse:
        """
        Synthesize text to speech (asynchronous).
        
        Returns TTSResponse with audio_url for the caller to use.
        """
        voice = voice or self.voice
        language = LANGUAGE_MAPPING.get(language, "Auto") if language else "Auto"
        model = model or self.model
        
        try:
            # Run in thread pool since dashscope SDK is synchronous
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: MultiModalConversation.call(
                    model=model,
                    api_key=self.api_key,
                    text=text,
                    voice=voice,
                    language_type=language,
                )
            )
            
            if response.status_code != 200:
                raise Exception(f"TTS API error: {response.code} - {response.message}")
            
            audio_info = response.output.audio
            
            return TTSResponse(
                audio_url=audio_info.get("url", ""),
                characters=response.usage.get("characters", 0) if response.usage else 0,
                expires_at=audio_info.get("expires_at"),
                request_id=response.request_id,
            )
            
        except Exception as e:
            self.logger.error(f"Async TTS synthesis error: {e}")
            raise
    
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Streaming text-to-speech synthesis.
        
        Note: This is a simplified implementation that yields the complete audio.
        For true streaming, you would need to use the DashScope streaming API.
        """
        voice = voice or self.voice
        language = kwargs.get("language", "Auto")
        
        try:
            # For now, use non-streaming and yield the result
            response = await self.synthesize_async(text, voice, language)
            
            if response.audio_url:
                # Yield the URL as a marker (caller should handle downloading)
                yield response.audio_url.encode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Stream TTS error: {e}")
            raise
    
    @staticmethod
    def get_available_voices() -> dict:
        """Get available voice options"""
        return QWEN_TTS_VOICES
    
    @staticmethod
    def get_supported_languages() -> list:
        """Get supported languages"""
        return list(set(LANGUAGE_MAPPING.values()))
