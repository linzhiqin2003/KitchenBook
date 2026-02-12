"""
Tingwu (通义听悟) Real-time ASR + Translation Service

Provides two components:
1. TingwuTaskManager — REST API wrapper for creating/stopping/querying tasks
2. TingwuRealtimeService — WebSocket wrapper using alibabacloud-nls SDK

Tingwu advantages over DashScope/Groq:
- Built-in real-time translation (no extra LLM call needed)
- Speaker diarization
- Multi-language support (cn, en, ja, yue, fspk)
"""

import json
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from common.config import get_settings

logger = logging.getLogger(__name__)


# --- REST API: Task Management ---

class TingwuTaskManager:
    """
    REST API wrapper for Tingwu real-time tasks.

    Uses aliyunsdkcore for request signing.
    """

    DOMAIN_TEMPLATE = "tingwu.{region}.aliyuncs.com"
    API_VERSION = "2023-09-30"
    URI = "/openapi/tingwu/v2/tasks"

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        app_key: Optional[str] = None,
        region: Optional[str] = None,
    ):
        settings = get_settings()
        self.access_key_id = access_key_id or settings.tingwu.access_key_id
        self.access_key_secret = access_key_secret or settings.tingwu.access_key_secret
        self.app_key = app_key or settings.tingwu.app_key
        self.region = region or settings.tingwu.region
        self.domain = self.DOMAIN_TEMPLATE.format(region=self.region)

        self._client = None

    def _get_client(self):
        if self._client is None:
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.auth.credentials import AccessKeyCredential

            credentials = AccessKeyCredential(self.access_key_id, self.access_key_secret)
            self._client = AcsClient(region_id=self.region, credential=credentials)
        return self._client

    def _make_request(self, method: str = "PUT", query_params: Optional[Dict] = None, body: Optional[Dict] = None):
        from aliyunsdkcore.request import CommonRequest

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain(self.domain)
        request.set_version(self.API_VERSION)
        request.set_protocol_type("https")
        request.set_method(method)
        request.set_uri_pattern(self.URI)
        request.add_header("Content-Type", "application/json")

        if query_params:
            for k, v in query_params.items():
                request.add_query_param(k, v)

        if body:
            request.set_content(json.dumps(body).encode("utf-8"))

        client = self._get_client()
        response = client.do_action_with_exception(request)
        return json.loads(response)

    def create_realtime_task(
        self,
        source_lang: str = "cn",
        enable_translation: bool = True,
        target_languages: Optional[List[str]] = None,
        sample_rate: int = 16000,
        audio_format: str = "pcm",
        diarization_enabled: bool = False,
        speaker_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a new real-time task.

        Returns:
            {
                "task_id": "...",
                "meeting_join_url": "wss://...",
                "task_status": "ONGOING",
            }
        """
        task_key = f"task_{uuid.uuid4().hex[:12]}"

        body: Dict[str, Any] = {
            "AppKey": self.app_key,
            "Input": {
                "Format": audio_format,
                "SampleRate": sample_rate,
                "SourceLanguage": source_lang,
                "TaskKey": task_key,
            },
            "Parameters": {
                "Transcription": {
                    "DiarizationEnabled": diarization_enabled,
                },
            },
        }

        if diarization_enabled and speaker_count > 0:
            body["Parameters"]["Transcription"]["Diarization"] = {
                "SpeakerCount": speaker_count,
            }

        if enable_translation and target_languages:
            body["Parameters"]["TranslationEnabled"] = True
            body["Parameters"]["Translation"] = {
                "TargetLanguages": target_languages,
            }

        logger.info(f"Creating Tingwu realtime task: source_lang={source_lang}, translation={enable_translation}")
        result = self._make_request(
            method="PUT",
            query_params={"type": "realtime"},
            body=body,
        )

        data = result.get("Data", {})
        return {
            "task_id": data.get("TaskId", ""),
            "task_key": task_key,
            "meeting_join_url": data.get("MeetingJoinUrl", ""),
            "task_status": data.get("TaskStatus", ""),
            "raw": result,
        }

    def stop_task(self, task_id: str) -> Dict[str, Any]:
        """Stop a running real-time task."""
        body = {
            "AppKey": self.app_key,
            "Input": {
                "TaskId": task_id,
            },
        }

        logger.info(f"Stopping Tingwu task: {task_id}")
        result = self._make_request(
            method="PUT",
            query_params={"type": "realtime", "operation": "stop"},
            body=body,
        )
        return result

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Query task status."""
        from aliyunsdkcore.request import CommonRequest

        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain(self.domain)
        request.set_version(self.API_VERSION)
        request.set_protocol_type("https")
        request.set_method("GET")
        request.set_uri_pattern(f"{self.URI}/{task_id}")
        request.add_header("Content-Type", "application/json")

        client = self._get_client()
        response = client.do_action_with_exception(request)
        return json.loads(response)


# --- WebSocket: Real-time Audio Streaming ---

class TingwuRealtimeService:
    """
    Real-time ASR + Translation service via Tingwu WebSocket.

    Uses alibabacloud-nls SDK's NlsRealtimeMeeting to connect to the
    MeetingJoinUrl returned by TingwuTaskManager.create_realtime_task().

    Events are pushed into a thread-safe queue (same pattern as RealtimeASRService).
    """

    def __init__(self, meeting_join_url: str):
        self.meeting_join_url = meeting_join_url
        self._meeting = None
        self._is_connected = False
        self._lock = threading.Lock()

        # Thread-safe event queue (same pattern as DashScope ASR)
        self.event_queue: queue.Queue = queue.Queue(maxsize=1000)

    def _put_event(self, event):
        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            logger.warning("Tingwu event queue full, dropping event")

    # --- NLS SDK Callbacks ---

    def _on_start(self, message, *args):
        logger.info(f"Tingwu connection started: {message}")
        from .asr_service import ASREvent, ASREventType
        self._is_connected = True
        self._put_event(ASREvent(ASREventType.CONNECTED))

    def _on_sentence_begin(self, message, *args):
        logger.debug(f"Tingwu sentence begin: {message}")
        from .asr_service import ASREvent, ASREventType
        self._put_event(ASREvent(ASREventType.SPEECH_START))

    def _on_result_changed(self, message, *args):
        """Intermediate transcription result."""
        from .asr_service import ASREvent, ASREventType, TranscriptionResult
        try:
            data = json.loads(message) if isinstance(message, str) else message
            # Tingwu returns payload.result or direct text
            text = self._extract_text(data)
            if text:
                result = TranscriptionResult(text=text, is_final=False)
                self._put_event(ASREvent(ASREventType.TRANSCRIPTION, result))
        except Exception as e:
            logger.error(f"Error parsing result_changed: {e}")

    def _on_sentence_end(self, message, *args):
        """Final transcription for a sentence."""
        from .asr_service import ASREvent, ASREventType, TranscriptionResult
        try:
            data = json.loads(message) if isinstance(message, str) else message
            text = self._extract_text(data)
            if text:
                result = TranscriptionResult(text=text, is_final=True)
                self._put_event(ASREvent(ASREventType.TRANSCRIPTION, result))
        except Exception as e:
            logger.error(f"Error parsing sentence_end: {e}")

    def _on_result_translated(self, message, *args):
        """Built-in translation result from Tingwu."""
        from .asr_service import ASREvent, ASREventType, TranslationResult
        try:
            data = json.loads(message) if isinstance(message, str) else message
            original = self._extract_text(data, key="text")
            translated = self._extract_text(data, key="translate")
            if translated:
                result = TranslationResult(
                    original_text=original or "",
                    translated_text=translated,
                    is_final=True,
                )
                self._put_event(ASREvent(ASREventType.TRANSLATION, result))
        except Exception as e:
            logger.error(f"Error parsing result_translated: {e}")

    def _on_completed(self, message, *args):
        logger.info(f"Tingwu completed: {message}")

    def _on_error(self, message, *args):
        logger.error(f"Tingwu error: {message}")
        from .asr_service import ASREvent, ASREventType
        friendly = self._parse_nls_error(message)
        self._put_event(ASREvent(ASREventType.ERROR, friendly))

    @staticmethod
    def _parse_nls_error(message) -> str:
        """Extract a user-friendly message from NLS SDK error JSON."""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            if isinstance(data, dict):
                header = data.get("header", {})
                status_text = header.get("status_text", "")
                status = header.get("status", 0)
                if "IDLE_TIMEOUT" in status_text:
                    return "听悟会话超时，请重新开始"
                if status_text:
                    return f"听悟错误: {status_text}"
                if status:
                    return f"听悟错误 ({status})"
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        return str(message)[:200]

    def _on_close(self, *args):
        logger.info("Tingwu connection closed")
        from .asr_service import ASREvent, ASREventType
        self._is_connected = False
        self._put_event(ASREvent(ASREventType.DISCONNECTED))

    # --- Helper ---

    @staticmethod
    def _extract_text(data: Any, key: str = "text") -> str:
        """Extract text from various Tingwu message formats."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data

        if isinstance(data, dict):
            # Try payload.result first (NLS format)
            payload = data.get("payload", {})
            if isinstance(payload, dict):
                result = payload.get("result", "")
                if result:
                    return result

            # Direct key lookup
            if key in data:
                return data[key]

            # Try header.name based structure
            header = data.get("header", {})
            if isinstance(header, dict) and header.get("name") in (
                "SentenceEnd", "SentenceBegin", "ResultChanged", "ResultTranslated"
            ):
                return payload.get(key, "")

        return ""

    # --- Public API ---

    def connect(self):
        """Connect to Tingwu real-time meeting via NLS SDK."""
        import nls

        self._meeting = nls.NlsRealtimeMeeting(
            url=self.meeting_join_url,
            on_sentence_begin=self._on_sentence_begin,
            on_sentence_end=self._on_sentence_end,
            on_start=self._on_start,
            on_result_changed=self._on_result_changed,
            on_result_translated=self._on_result_translated,
            on_completed=self._on_completed,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        r = self._meeting.start()
        if r is not True and r is not None:
            logger.warning(f"Tingwu meeting start returned: {r}")

        logger.info("Tingwu realtime service connected")
        return self.event_queue

    _send_count = 0

    def send_audio(self, audio_data: bytes):
        """Send raw audio bytes (PCM) to Tingwu."""
        with self._lock:
            if not self._is_connected or not self._meeting:
                logger.warning("Tingwu not connected, dropping audio (%d bytes)", len(audio_data))
                return
            try:
                self._send_count += 1
                self._meeting.send_audio(audio_data)
                if self._send_count <= 3 or self._send_count % 50 == 0:
                    logger.info(f"[Tingwu] send_audio #{self._send_count}: {len(audio_data)} bytes sent to NLS")
            except Exception as e:
                logger.error(f"Error sending audio to Tingwu: {e}")
                from .asr_service import ASREvent, ASREventType
                self._put_event(ASREvent(ASREventType.ERROR, str(e)))

    def stop(self):
        """Stop the NLS meeting connection."""
        with self._lock:
            if self._meeting:
                try:
                    self._meeting.stop()
                except Exception as e:
                    logger.warning(f"Error stopping Tingwu meeting: {e}")
                self._is_connected = False
                self._meeting = None
                logger.info("Tingwu realtime service stopped")

    def get_all_events(self) -> list:
        """Get all pending events from the queue (non-blocking)."""
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
        return self._is_connected
