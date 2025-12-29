"""
Real-time ASR Service using DashScope Qwen-ASR-Realtime API

This module uses a thread-safe queue to communicate between the DashScope SDK's
synchronous callback thread and Django Channels' async consumer.
"""

import asyncio
import base64
import logging
import queue
import threading
from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum

from dashscope.audio.qwen_omni import (
    OmniRealtimeConversation,
    OmniRealtimeCallback,
    MultiModality,
)
from dashscope.audio.qwen_omni.omni_realtime import TranscriptionParams

from common.config import get_settings

# Set up logging
logger = logging.getLogger(__name__)


class ASREventType(Enum):
    """Types of ASR events"""
    TRANSCRIPTION = "transcription"
    SPEECH_START = "speech_start"
    SPEECH_STOP = "speech_stop"
    ERROR = "error"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass
class ASREvent:
    """Event from ASR service"""
    event_type: ASREventType
    data: Any = None


@dataclass
class TranscriptionResult:
    """Represents a transcription result"""
    text: str
    is_final: bool
    language: Optional[str] = None
    timestamp: Optional[float] = None


class ASRCallback(OmniRealtimeCallback):
    """
    Callback handler for real-time ASR events.
    
    This callback is invoked from the SDK's websocket thread.
    We use a thread-safe queue to pass events to the async consumer.
    """

    def __init__(self, event_queue: queue.Queue):
        self.event_queue = event_queue
        self.conversation: Optional[OmniRealtimeConversation] = None

        # Event handlers mapping
        self.handlers = {
            'session.created': self._handle_session_created,
            'session.updated': self._handle_session_updated,
            'conversation.item.input_audio_transcription.completed': self._handle_final_text,
            'conversation.item.input_audio_transcription.text': self._handle_stash_text,
            'input_audio_buffer.speech_started': self._handle_speech_start,
            'input_audio_buffer.speech_stopped': self._handle_speech_stop,
            'input_audio_buffer.committed': self._handle_audio_committed,
            'error': self._handle_error,
        }

    def _put_event(self, event: ASREvent):
        """Thread-safe method to put events in the queue"""
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            logger.warning("Event queue full, dropping event")

    def on_open(self):
        """WebSocket connection opened"""
        logger.info("ASR WebSocket connection opened")
        self._put_event(ASREvent(ASREventType.CONNECTED))

    def on_close(self, code: int, msg: str):
        """WebSocket connection closed"""
        logger.info(f"ASR WebSocket connection closed - Code: {code}, Message: {msg}")
        self._put_event(ASREvent(ASREventType.DISCONNECTED, {"code": code, "message": msg}))

    def on_event(self, response: dict):
        """Handle incoming events from the server"""
        try:
            event_type = response.get('type', 'unknown')
            handler = self.handlers.get(event_type)
            if handler:
                handler(response)
            else:
                logger.debug(f"Unhandled event type: {event_type}")
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            self._put_event(ASREvent(ASREventType.ERROR, str(e)))

    def _handle_session_created(self, response: dict):
        """Handle session creation"""
        session_id = response.get('session', {}).get('id', 'unknown')
        logger.info(f"ASR Session created: {session_id}")

    def _handle_session_updated(self, response: dict):
        """Handle session update"""
        logger.info("ASR Session configuration updated")

    def _handle_final_text(self, response: dict):
        """Handle final transcription result"""
        transcript = response.get('transcript', '')
        logger.info(f"Final transcription: {transcript}")
        if transcript:
            result = TranscriptionResult(text=transcript, is_final=True)
            self._put_event(ASREvent(ASREventType.TRANSCRIPTION, result))

    def _handle_stash_text(self, response: dict):
        """Handle intermediate transcription result"""
        stash = response.get('stash', '')
        logger.debug(f"Intermediate transcription: {stash}")
        if stash:
            result = TranscriptionResult(text=stash, is_final=False)
            self._put_event(ASREvent(ASREventType.TRANSCRIPTION, result))

    def _handle_speech_start(self, response: dict):
        """Handle speech start detection"""
        logger.info("Speech started")
        self._put_event(ASREvent(ASREventType.SPEECH_START))

    def _handle_speech_stop(self, response: dict):
        """Handle speech stop detection"""
        logger.info("Speech stopped")
        self._put_event(ASREvent(ASREventType.SPEECH_STOP))

    def _handle_audio_committed(self, response: dict):
        """Handle audio buffer committed"""
        logger.debug("Audio buffer committed")

    def _handle_error(self, response: dict):
        """Handle error events"""
        error_msg = response.get('error', {}).get('message', 'Unknown error')
        logger.error(f"ASR Server error: {error_msg}")
        self._put_event(ASREvent(ASREventType.ERROR, error_msg))


class RealtimeASRService:
    """
    Real-time ASR Service wrapper with thread-safe event queue.
    
    This service runs the DashScope SDK in a separate thread and uses
    a queue to communicate events back to the async consumer.
    """

    def __init__(
        self,
        language: str = "en",
        model: Optional[str] = None,
        sample_rate: int = 16000,
        input_format: str = "pcm",
        vad_enabled: bool = True,
        vad_threshold: float = 0.2,
        vad_silence_ms: int = 800,
    ):
        # Get settings
        settings = get_settings()
        
        self.api_key = settings.api.dashscope_api_key
        self.model = model or settings.asr.model
        self.url = settings.asr.url
        self.language = language
        self.sample_rate = sample_rate
        self.input_format = input_format
        self.vad_enabled = vad_enabled
        self.vad_threshold = vad_threshold
        self.vad_silence_ms = vad_silence_ms

        self.conversation: Optional[OmniRealtimeConversation] = None
        self.callback: Optional[ASRCallback] = None
        self._is_connected = False
        self._lock = threading.Lock()
        
        # Thread-safe queue for events (max 1000 events)
        self.event_queue: queue.Queue = queue.Queue(maxsize=1000)

    def connect(self):
        """
        Connect to the ASR service and start a session.
        
        Returns the event queue that consumers should poll for events.
        """
        # Create callback handler with queue
        self.callback = ASRCallback(self.event_queue)

        # Create conversation instance
        self.conversation = OmniRealtimeConversation(
            model=self.model,
            url=self.url,
            callback=self.callback,
        )

        # Inject conversation reference to callback
        self.callback.conversation = self.conversation

        # Connect to the service
        self.conversation.connect()

        # Configure the session
        transcription_params = TranscriptionParams(
            language=self.language,
            sample_rate=self.sample_rate,
            input_audio_format=self.input_format,
        )

        self.conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_turn_detection=self.vad_enabled,
            turn_detection_type="server_vad",
            turn_detection_threshold=self.vad_threshold,
            turn_detection_silence_duration_ms=self.vad_silence_ms,
            transcription_params=transcription_params,
        )

        self._is_connected = True
        logger.info("ASR service connected and configured")
        
        return self.event_queue

    def send_audio(self, audio_data: bytes):
        """
        Send audio data to the ASR service (thread-safe).
        
        Args:
            audio_data: Raw audio bytes (PCM format)
        """
        with self._lock:
            if not self._is_connected or not self.conversation:
                logger.warning("Not connected to ASR service")
                return

            try:
                # Encode audio to base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                self.conversation.append_audio(audio_b64)
            except Exception as e:
                logger.error(f"Error sending audio: {e}")
                self.event_queue.put_nowait(ASREvent(ASREventType.ERROR, str(e)))

    def commit_audio(self):
        """Manually commit audio buffer (only when VAD is disabled)"""
        with self._lock:
            if not self._is_connected or not self.conversation:
                return
            if not self.vad_enabled:
                self.conversation.commit()

    def disconnect(self):
        """Disconnect from the ASR service"""
        with self._lock:
            if self.conversation:
                try:
                    self.conversation.close()
                except Exception as e:
                    logger.warning(f"Error closing ASR connection: {e}")
                self._is_connected = False
                self.conversation = None
                logger.info("ASR service disconnected")

    def get_event(self, timeout: float = 0.1) -> Optional[ASREvent]:
        """Get an event from the queue with timeout"""
        try:
            return self.event_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_all_events(self) -> list:
        """Get all pending events from the queue (non-blocking)"""
        events = []
        while True:
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except queue.Empty:
                break
        return events

    @property
    def is_connected(self) -> bool:
        """Check if connected to the service"""
        return self._is_connected
