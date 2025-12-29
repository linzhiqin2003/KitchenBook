"""
AI Provider Base Classes

This module defines abstract base classes for AI service providers,
enabling a unified interface for different AI services (LLM, ASR, TTS, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Types of AI service providers"""
    DASHSCOPE = "dashscope"      # Aliyun DashScope (Qwen models)
    OPENAI = "openai"            # OpenAI API
    AZURE = "azure"              # Azure AI Services
    ANTHROPIC = "anthropic"      # Anthropic (Claude)
    GOOGLE = "google"            # Google AI (Gemini)
    LOCAL = "local"              # Local models (Ollama, vLLM, etc.)


class ServiceType(Enum):
    """Types of AI services"""
    LLM = "llm"                  # Large Language Model (chat, completion)
    ASR = "asr"                  # Automatic Speech Recognition
    TTS = "tts"                  # Text-to-Speech
    TRANSLATION = "translation"  # Machine Translation
    IMAGE_GEN = "image_gen"      # Image Generation
    VISION = "vision"            # Image Understanding
    EMBEDDING = "embedding"      # Text Embedding
    REALTIME = "realtime"        # Real-time multimodal


@dataclass
class ProviderConfig:
    """Base configuration for AI providers"""
    provider_type: ProviderType
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Set default base URLs based on provider type
        if self.base_url is None:
            default_urls = {
                ProviderType.DASHSCOPE: "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ProviderType.OPENAI: "https://api.openai.com/v1",
                ProviderType.AZURE: None,  # Requires custom endpoint
                ProviderType.ANTHROPIC: "https://api.anthropic.com",
                ProviderType.GOOGLE: "https://generativelanguage.googleapis.com/v1beta",
            }
            self.base_url = default_urls.get(self.provider_type)


@dataclass
class Message:
    """A chat message"""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    role: str = "assistant"
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


@dataclass
class ASRResult:
    """Result from ASR service"""
    text: str
    is_final: bool
    language: Optional[str] = None
    confidence: Optional[float] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None


@dataclass
class TTSResult:
    """Result from TTS service"""
    audio_data: bytes
    format: str = "pcm"
    sample_rate: int = 16000


@dataclass
class TranslationResult:
    """Result from translation service"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: Optional[float] = None


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    Subclasses should implement specific service methods based on
    the services they support.
    """
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def provider_type(self) -> ProviderType:
        return self.config.provider_type
    
    @abstractmethod
    def get_supported_services(self) -> List[ServiceType]:
        """Return list of services this provider supports"""
        pass
    
    def supports_service(self, service_type: ServiceType) -> bool:
        """Check if this provider supports a specific service"""
        return service_type in self.get_supported_services()


class LLMProvider(BaseProvider):
    """Base class for LLM providers"""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Synchronous chat completion"""
        pass
    
    @abstractmethod
    async def chat_async(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Asynchronous chat completion"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Streaming chat completion"""
        pass


class ASRProvider(BaseProvider):
    """Base class for ASR (Speech Recognition) providers"""
    
    @abstractmethod
    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs
    ) -> ASRResult:
        """Transcribe audio file"""
        pass
    
    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[ASRResult]:
        """Real-time streaming transcription"""
        pass


class TTSProvider(BaseProvider):
    """Base class for TTS (Text-to-Speech) providers"""
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        **kwargs
    ) -> TTSResult:
        """Synthesize text to speech"""
        pass
    
    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Streaming text-to-speech synthesis"""
        pass


class TranslationProvider(BaseProvider):
    """Base class for Translation providers"""
    
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en",
        **kwargs
    ) -> TranslationResult:
        """Translate text"""
        pass
    
    @abstractmethod
    async def translate_async(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en",
        **kwargs
    ) -> TranslationResult:
        """Async translate text"""
        pass
