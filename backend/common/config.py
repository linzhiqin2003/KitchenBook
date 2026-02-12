"""
Centralized Configuration Management

Manages all application settings with support for:
- Environment variables
- .env files
- Runtime configuration
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()  # Try default locations


@dataclass
class APIConfig:
    """API provider configuration"""
    # DashScope (Aliyun)
    dashscope_api_key: str = field(
        default_factory=lambda: os.environ.get("DASHSCOPE_API_KEY", "")
    )
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_http_api_url: str = field(
        default_factory=lambda: os.environ.get(
            "DASHSCOPE_HTTP_API_URL",
            "https://dashscope.aliyuncs.com/api/v1"  # China region
        )
    )
    dashscope_file_asr_model: str = field(
        default_factory=lambda: os.environ.get(
            "DASHSCOPE_FILE_ASR_MODEL",
            "fun-asr"
        )
    )
    
    # OpenAI
    openai_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    openai_base_url: str = field(
        default_factory=lambda: os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )
    
    # Azure OpenAI
    azure_api_key: str = field(
        default_factory=lambda: os.environ.get("AZURE_OPENAI_API_KEY", "")
    )
    azure_endpoint: str = field(
        default_factory=lambda: os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    )
    azure_api_version: str = "2024-02-15-preview"
    
    # Anthropic
    anthropic_api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )

    # Groq
    groq_api_key: str = field(
        default_factory=lambda: os.environ.get("GROQ_API_KEY", "")
    )

    # Cerebras
    cerebras_api_key: str = field(
        default_factory=lambda: os.environ.get("CEREBRAS_API_KEY", "")
    )
    groq_asr_model: str = field(
        default_factory=lambda: os.environ.get("GROQ_ASR_MODEL", "whisper-large-v3")
    )


@dataclass
class TingwuConfig:
    """Tingwu (通义听悟) configuration"""
    access_key_id: str = field(
        default_factory=lambda: os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    )
    access_key_secret: str = field(
        default_factory=lambda: os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    )
    app_key: str = field(
        default_factory=lambda: os.environ.get("TINGWU_APP_KEY", "")
    )
    region: str = field(
        default_factory=lambda: os.environ.get("TINGWU_REGION", "cn-beijing")
    )


@dataclass
class ASRConfig:
    """ASR (Speech Recognition) configuration"""
    model: str = "qwen3-asr-flash-realtime"
    url: str = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
    sample_rate: int = 16000
    input_format: str = "pcm"
    channels: int = 1
    
    # VAD settings - tuned for sentence-level detection
    vad_enabled: bool = True
    vad_type: str = "server_vad"
    vad_threshold: float = 0.15  # Lower = more sensitive to speech end
    vad_silence_ms: int = 400    # Reduced from 800ms for faster sentence breaks


@dataclass
class TranslationConfig:
    """Translation configuration"""
    model: str = "qwen-mt-turbo"
    source_lang: str = "auto"
    target_lang: str = "Chinese"
    temperature: float = 0.65
    top_p: float = 0.8


@dataclass
class LLMConfig:
    """LLM configuration"""
    default_model: str = "qwen-plus"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 0.95


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = field(
        default_factory=lambda: os.environ.get("HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("PORT", "8000"))
    )
    debug: bool = field(
        default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true"
    )
    allowed_hosts: List[str] = field(
        default_factory=lambda: os.environ.get("ALLOWED_HOSTS", "*").split(",")
    )
    cors_origins: List[str] = field(
        default_factory=lambda: os.environ.get(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://localhost:3000"
        ).split(",")
    )


@dataclass
class AppSettings:
    """
    Main application settings container.
    
    Groups all configuration into logical sections.
    """
    api: APIConfig = field(default_factory=APIConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    tingwu: TingwuConfig = field(default_factory=TingwuConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings.
        """
        warnings = []
        
        if not self.api.dashscope_api_key:
            warnings.append("DASHSCOPE_API_KEY is not set")
        
        return warnings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)"""
        return {
            "api": {
                "dashscope_configured": bool(self.api.dashscope_api_key),
                "openai_configured": bool(self.api.openai_api_key),
                "azure_configured": bool(self.api.azure_api_key),
            },
            "asr": {
                "model": self.asr.model,
                "sample_rate": self.asr.sample_rate,
                "vad_enabled": self.asr.vad_enabled,
            },
            "translation": {
                "model": self.translation.model,
                "default_target": self.translation.target_lang,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "debug": self.server.debug,
            },
        }


# Singleton settings instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get the application settings singleton"""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


def reload_settings() -> AppSettings:
    """Reload settings from environment"""
    global _settings
    load_dotenv(override=True)
    _settings = AppSettings()
    return _settings


# Language mappings for UI
SUPPORTED_LANGUAGES = {
    "zh": {"name": "中文", "english": "Chinese"},
    "yue": {"name": "粤语", "english": "Cantonese"},
    "en": {"name": "English", "english": "English"},
    "ja": {"name": "日本語", "english": "Japanese"},
    "ko": {"name": "한국어", "english": "Korean"},
    "de": {"name": "Deutsch", "english": "German"},
    "fr": {"name": "Français", "english": "French"},
    "es": {"name": "Español", "english": "Spanish"},
    "ru": {"name": "Русский", "english": "Russian"},
    "pt": {"name": "Português", "english": "Portuguese"},
    "ar": {"name": "العربية", "english": "Arabic"},
    "it": {"name": "Italiano", "english": "Italian"},
    "hi": {"name": "हिन्दी", "english": "Hindi"},
    "id": {"name": "Bahasa Indonesia", "english": "Indonesian"},
    "th": {"name": "ภาษาไทย", "english": "Thai"},
    "tr": {"name": "Türkçe", "english": "Turkish"},
    "uk": {"name": "Українська", "english": "Ukrainian"},
    "vi": {"name": "Tiếng Việt", "english": "Vietnamese"},
}


def get_language_name(code: str, english: bool = False) -> str:
    """Get language name from code"""
    lang = SUPPORTED_LANGUAGES.get(code, {})
    if english:
        return lang.get("english", code)
    return lang.get("name", code)
