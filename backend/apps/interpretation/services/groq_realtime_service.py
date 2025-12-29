"""
Groq-based Real-time ASR Service

Uses Groq's Whisper API for high-speed transcription.
Audio is collected in chunks and sent for processing.
"""

import os
import logging
import tempfile
import wave
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import openai
except ImportError:
    openai = None

from common.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GroqTranscriptionResult:
    """Result from Groq transcription"""
    text: str
    is_final: bool = True
    duration: Optional[float] = None


class GroqRealtimeASRService:
    """
    Real-time ASR Service using Groq Whisper API.
    
    Collects audio chunks and sends them for transcription
    when enough data is accumulated or silence is detected.
    """
    
    def __init__(
        self,
        language: str = "en",
        model: str = "whisper-large-v3",
        sample_rate: int = 16000,
        chunk_duration_s: float = 4.0,  # Send audio every N seconds (longer = better sentence detection)
    ):
        settings = get_settings()
        
        self.api_key = settings.api.groq_api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.language = language
        self.sample_rate = sample_rate
        self.chunk_duration_s = chunk_duration_s
        self.channels = 1
        self.sample_width = 2  # 16-bit PCM
        
        # Audio buffer
        self._audio_buffer = bytearray()
        self._min_chunk_bytes = int(sample_rate * chunk_duration_s * self.sample_width)
        
        # OpenAI client for Groq
        self._client = None
        if openai and self.api_key:
            self._client = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.api_key
            )
    
    def add_audio(self, audio_data: bytes) -> Optional[GroqTranscriptionResult]:
        """
        Add audio data to buffer. Returns transcription if buffer is full.
        
        This is a synchronous method - for async, use add_audio_async.
        """
        self._audio_buffer.extend(audio_data)
        
        # Check if we have enough audio to process
        if len(self._audio_buffer) >= self._min_chunk_bytes:
            return self._process_buffer()
        
        return None
    
    async def add_audio_async(self, audio_data: bytes) -> Optional[GroqTranscriptionResult]:
        """Async version of add_audio"""
        self._audio_buffer.extend(audio_data)
        
        if len(self._audio_buffer) >= self._min_chunk_bytes:
            # Run transcription in thread pool
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._process_buffer)
        
        return None
    
    def flush(self) -> Optional[GroqTranscriptionResult]:
        """Process any remaining audio in buffer"""
        if len(self._audio_buffer) > 0:
            return self._process_buffer()
        return None
    
    async def flush_async(self) -> Optional[GroqTranscriptionResult]:
        """Async version of flush"""
        if len(self._audio_buffer) > 0:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._process_buffer)
        return None
    
    def _process_buffer(self) -> Optional[GroqTranscriptionResult]:
        """Process current audio buffer with Groq Whisper"""
        if not self._client:
            logger.error("Groq client not initialized (missing API key?)")
            return None
        
        if len(self._audio_buffer) < 100:  # Too small to process
            self._audio_buffer.clear()
            return None
        
        try:
            # Save buffer to temp WAV file
            audio_bytes = bytes(self._audio_buffer)
            self._audio_buffer.clear()
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp, 'wb') as wav:
                    wav.setnchannels(self.channels)
                    wav.setsampwidth(self.sample_width)
                    wav.setframerate(self.sample_rate)
                    wav.writeframes(audio_bytes)
            
            # Send to Groq
            with open(tmp_path, "rb") as audio_file:
                response = self._client.audio.transcriptions.create(
                    file=audio_file,
                    model=self.model,
                    language=self.language if self.language != "auto" else None,
                    response_format="json",
                    temperature=0.0
                )
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            text = response.text.strip()
            if text:
                logger.info(f"Groq transcription: {text}")
                return GroqTranscriptionResult(
                    text=text,
                    is_final=True,
                    duration=len(audio_bytes) / (self.sample_rate * self.sample_width)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Groq transcription error: {e}")
            return None
    
    def reset(self):
        """Clear audio buffer"""
        self._audio_buffer.clear()


class GroqTranslationService:
    """
    Translation service using Groq's LLM for high-speed translation.
    """
    
    # Strict system prompt to prevent extra output
    SYSTEM_PROMPT = """You are a translation engine. Your ONLY task is to translate the input text.

RULES:
1. Output ONLY the translated text
2. Do NOT add any explanations, notes, or comments
3. Do NOT add quotation marks around the translation
4. Do NOT include the original text
5. Do NOT say things like "Here's the translation:" or "Translation:"
6. Preserve the original formatting (capitalization, punctuation)
7. If the input is empty or just punctuation, output the same

Target language: {target_lang}"""
    
    def __init__(
        self,
        model: str = "openai/gpt-oss-20b",  # Groq GPT-OSS 20B for fast translation
        target_lang: str = "Chinese",
    ):
        settings = get_settings()
        
        self.api_key = settings.api.groq_api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.target_lang = target_lang
        
        # OpenAI client for Groq
        self._client = None
        if openai and self.api_key:
            self._client = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.api_key
            )
    
    def translate(self, text: str, source_lang: str = "auto", target_lang: str = None) -> Dict[str, Any]:
        """Synchronous translation"""
        target = target_lang or self.target_lang
        
        if not self._client:
            return {"success": False, "error": "Groq client not initialized"}
        
        if not text.strip():
            return {"success": False, "error": "Empty text"}
        
        try:
            # Use strict system prompt
            system_prompt = self.SYSTEM_PROMPT.format(target_lang=target)
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,  # Lower temperature for more consistent output
                max_tokens=1024
            )
            
            translated = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated,
                "source_lang": source_lang,
                "target_lang": target,
            }
            
        except Exception as e:
            logger.error(f"Groq translation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def translate_async(self, text: str, source_lang: str = "auto", target_lang: str = None) -> Dict[str, Any]:
        """Async translation"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.translate, text, source_lang, target_lang)
