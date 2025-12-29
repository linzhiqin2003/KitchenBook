"""
WebSocket Consumer for ASR and Translation

Uses thread-safe queue polling to receive events from the ASR service.
Supports both DashScope (default) and Groq (high-speed) providers.
"""

import asyncio
import base64
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

# Use relative imports within the app
from .services.asr_service import RealtimeASRService, ASREvent, ASREventType, TranscriptionResult
from .services.translation_service import TranslationService
from .services.tts_service import TTSService, TTSConfig
from .services.groq_realtime_service import GroqRealtimeASRService, GroqTranslationService

# Use common config
from common.config import get_settings

logger = logging.getLogger(__name__)


class ASRConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time ASR with translation and TTS
    
    Flow:
    1. Client sends audio data
    2. ASR service transcribes to text (via queue polling)
    3. Translation service translates to target language
    4. TTS service synthesizes speech (optional)
    5. Results sent back to client
    
    Supports two providers:
    - 'dashscope': DashScope Qwen-Realtime (default, lower latency stream)
    - 'groq': Groq Whisper + LLM (high-speed, chunk-based)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asr_service = None
        self.groq_asr_service = None  # For Groq high-speed mode
        self.groq_translation_service = None
        self.translation_service = None
        self.tts_service = None
        self.source_lang = 'en'
        self.target_lang = 'Chinese'
        self.translation_enabled = True
        self.tts_enabled = False  # TTS is off by default
        self.tts_voice = 'Cherry'  # Default voice
        self.provider = 'dashscope'  # 'dashscope' or 'groq'
        self._running = False
        self._poll_task = None

    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")
        
        await self.send_json({
            'type': 'connected',
            'message': 'WebSocket connected. Send "start" to begin ASR.'
        })

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")
        await self.stop_services()

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages"""
        if bytes_data:
            # Binary audio data
            await self.handle_audio(bytes_data)
            return
        
        if text_data:
            try:
                data = json.loads(text_data)
                await self.handle_message(data)
            except json.JSONDecodeError:
                await self.send_json({
                    'type': 'error',
                    'message': 'Invalid JSON'
                })

    async def handle_message(self, data):
        """Handle JSON messages from client"""
        msg_type = data.get('type', '')
        
        if msg_type == 'start':
            await self.start_services(data)
        elif msg_type == 'stop':
            await self.stop_services()
        elif msg_type == 'audio':
            # Base64 encoded audio
            audio_b64 = data.get('audio', '')
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
                await self.handle_audio(audio_bytes)
        elif msg_type == 'config':
            await self.update_config(data)
        elif msg_type == 'ping':
            await self.send_json({'type': 'pong'})
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def start_services(self, config):
        """Initialize and start ASR, translation, and TTS services"""
        try:
            # Get configuration from message
            self.source_lang = config.get('source_lang', 'en')
            self.target_lang = config.get('target_lang', 'Chinese')
            self.translation_enabled = config.get('translation_enabled', True)
            self.tts_enabled = config.get('tts_enabled', False)
            self.tts_voice = config.get('tts_voice', 'Cherry')
            self.provider = config.get('provider', 'dashscope')  # 'dashscope' or 'groq'
            
            # Get app settings
            settings = get_settings()
            
            if self.provider == 'groq':
                # === GROQ HIGH-SPEED MODE ===
                logger.info("Starting Groq high-speed mode")
                
                # Initialize Groq ASR service
                self.groq_asr_service = GroqRealtimeASRService(
                    language=self.source_lang,
                    model="whisper-large-v3",
                    chunk_duration_s=4.0,  # Process every 4 seconds for better sentence detection
                )
                
                # Initialize Groq Translation service
                if self.translation_enabled:
                    self.groq_translation_service = GroqTranslationService(
                        model="openai/gpt-oss-20b",  # Groq GPT-OSS 20B for fast translation
                        target_lang=self.target_lang,
                    )
                
                self._running = True
                
                await self.send_json({
                    'type': 'started',
                    'message': 'Groq high-speed services started',
                    'config': {
                        'source_lang': self.source_lang,
                        'target_lang': self.target_lang,
                        'translation_enabled': self.translation_enabled,
                        'tts_enabled': False,  # TTS not supported in Groq mode yet
                        'provider': 'groq',
                    }
                })
                
                logger.info(f"Groq services started: ASR({self.source_lang}) -> Translation({self.target_lang})")
                
            else:
                # === DASHSCOPE MODE (default) ===
                # Initialize translation service with target language
                self.translation_service = TranslationService(
                    target_lang=self.target_lang
                )
                
                # Initialize TTS service if enabled
                if self.tts_enabled:
                    tts_config = TTSConfig(
                        voice=self.tts_voice,
                        language=self.target_lang,
                    )
                    self.tts_service = TTSService(config=tts_config)
                    logger.info(f"TTS service initialized with voice: {self.tts_voice}")
                
                # Initialize ASR service with source language and VAD settings from config
                self.asr_service = RealtimeASRService(
                    language=self.source_lang,
                    vad_enabled=settings.asr.vad_enabled,
                    vad_threshold=settings.asr.vad_threshold,
                    vad_silence_ms=settings.asr.vad_silence_ms,
                )
                
                # Connect ASR (returns the event queue)
                self.asr_service.connect()
                
                self._running = True
                
                # Start the event polling task
                self._poll_task = asyncio.create_task(self._poll_asr_events())
                
                await self.send_json({
                    'type': 'started',
                    'message': 'ASR, translation, and TTS services started',
                    'config': {
                        'source_lang': self.source_lang,
                        'target_lang': self.target_lang,
                        'translation_enabled': self.translation_enabled,
                        'tts_enabled': self.tts_enabled,
                        'tts_voice': self.tts_voice,
                        'provider': 'dashscope',
                    }
                })
                
                logger.info(f"DashScope services started: ASR({self.source_lang}) -> Translation({self.target_lang}) -> TTS({self.tts_enabled})")
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}", exc_info=True)
            await self.send_json({
                'type': 'error',
                'message': f'Failed to start services: {str(e)}'
            })

    async def stop_services(self):
        """Stop ASR, translation, and TTS services"""
        self._running = False
        
        # Cancel the polling task
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        
        # Disconnect DashScope ASR
        if self.asr_service:
            self.asr_service.disconnect()
            self.asr_service = None
        
        # Clean up Groq services
        if self.groq_asr_service:
            self.groq_asr_service.reset()
            self.groq_asr_service = None
        self.groq_translation_service = None
        
        self.translation_service = None
        self.tts_service = None
        
        await self.send_json({
            'type': 'stopped',
            'message': 'Services stopped'
        })
        
        logger.info("Services stopped")

    async def update_config(self, data):
        """Update configuration without restarting"""
        if 'target_lang' in data:
            self.target_lang = data['target_lang']
        if 'translation_enabled' in data:
            self.translation_enabled = data['translation_enabled']
        if 'tts_enabled' in data:
            self.tts_enabled = data['tts_enabled']
            # Initialize or clear TTS service based on new setting
            if self.tts_enabled and not self.tts_service:
                tts_config = TTSConfig(
                    voice=self.tts_voice,
                    language=self.target_lang,
                )
                self.tts_service = TTSService(config=tts_config)
                logger.info(f"TTS service enabled with voice: {self.tts_voice}")
            elif not self.tts_enabled:
                self.tts_service = None
                logger.info("TTS service disabled")
        if 'tts_voice' in data:
            self.tts_voice = data['tts_voice']
            if self.tts_service:
                self.tts_service.config.voice = self.tts_voice
        
        await self.send_json({
            'type': 'config_updated',
            'config': {
                'target_lang': self.target_lang,
                'translation_enabled': self.translation_enabled,
                'tts_enabled': self.tts_enabled,
                'tts_voice': self.tts_voice,
            }
        })

    async def handle_audio(self, audio_bytes):
        """Handle incoming audio data"""
        if not self._running:
            return
            
        if self.provider == 'groq' and self.groq_asr_service:
            # === GROQ MODE: Chunk-based processing ===
            result = await self.groq_asr_service.add_audio_async(audio_bytes)
            
            if result and result.text:
                # Send transcription immediately
                await self.send_json({
                    'type': 'transcription',
                    'text': result.text,
                    'is_final': True,
                })
                
                # Translate if enabled
                if self.translation_enabled and self.groq_translation_service:
                    trans_result = await self.groq_translation_service.translate_async(
                        result.text,
                        source_lang=self.source_lang,
                        target_lang=self.target_lang
                    )
                    
                    if trans_result.get("success"):
                        await self.send_json({
                            'type': 'translation',
                            'original': trans_result['original_text'],
                            'translated': trans_result['translated_text'],
                            'target_lang': trans_result['target_lang'],
                        })
                    else:
                        logger.error(f"Groq translation error: {trans_result.get('error')}")
                        
        elif self.asr_service:
            # === DASHSCOPE MODE: Stream-based processing ===
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.asr_service.send_audio, audio_bytes)

    async def _poll_asr_events(self):
        """Poll the ASR event queue and process events"""
        logger.info("Started ASR event polling")
        
        while self._running:
            try:
                # Get all pending events (non-blocking)
                if self.asr_service:
                    events = self.asr_service.get_all_events()
                    
                    for event in events:
                        await self._handle_asr_event(event)
                
                # Small sleep to prevent busy-waiting
                await asyncio.sleep(0.05)
                
            except asyncio.CancelledError:
                logger.info("ASR event polling cancelled")
                break
            except Exception as e:
                logger.error(f"Error in ASR event polling: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("ASR event polling stopped")

    async def _handle_asr_event(self, event: ASREvent):
        """Handle an ASR event"""
        try:
            if event.event_type == ASREventType.TRANSCRIPTION:
                await self.on_transcription(event.data)
            elif event.event_type == ASREventType.SPEECH_START:
                await self.on_speech_start()
            elif event.event_type == ASREventType.SPEECH_STOP:
                await self.on_speech_stop()
            elif event.event_type == ASREventType.ERROR:
                await self.on_error(event.data)
            elif event.event_type == ASREventType.CONNECTED:
                logger.info("ASR connection confirmed")
            elif event.event_type == ASREventType.DISCONNECTED:
                logger.info(f"ASR disconnected: {event.data}")
        except Exception as e:
            logger.error(f"Error handling ASR event: {e}")

    async def on_transcription(self, result: TranscriptionResult):
        """Handle transcription result from ASR"""
        try:
            # Send original transcription
            await self.send_json({
                'type': 'transcription',
                'text': result.text,
                'is_final': result.is_final,
            })
            
            # Translate if enabled and is final result
            if self.translation_enabled and result.is_final and result.text.strip():
                await self.translate_and_send(result.text)
                
        except Exception as e:
            logger.error(f"Error in on_transcription: {e}")

    async def translate_and_send(self, text):
        """Translate text, synthesize speech, and send results"""
        if not self.translation_service:
            return
        
        try:
            result = await self.translation_service.translate_async(
                text,
                source_lang='auto',
                target_lang=self.target_lang
            )
            
            # Base translation message
            translation_msg = {
                'type': 'translation',
                'original': result.original_text,
                'translated': result.translated_text,
                'target_lang': result.target_lang,
            }
            
            # Log TTS status
            logger.info(f"TTS check: enabled={self.tts_enabled}, service={self.tts_service is not None}, text='{result.translated_text[:50] if result.translated_text else ''}'")
            
            # Synthesize speech if TTS is enabled
            if self.tts_enabled and self.tts_service and result.translated_text.strip():
                try:
                    logger.info(f"Calling TTS with voice={self.tts_voice}, language={self.target_lang}")
                    tts_result = await self.tts_service.synthesize(
                        text=result.translated_text,
                        voice=self.tts_voice,
                        language=self.target_lang,
                    )
                    
                    logger.info(f"TTS result: {tts_result}")
                    
                    if tts_result.get("success"):
                        translation_msg['audio_url'] = tts_result.get("audio_url")
                        translation_msg['audio_expires_at'] = tts_result.get("expires_at")
                        logger.info(f"TTS synthesis successful: {tts_result.get('characters')} chars, url={tts_result.get('audio_url')[:80]}")
                    else:
                        logger.warning(f"TTS synthesis failed: {tts_result.get('error')}")
                        
                except Exception as tts_error:
                    logger.error(f"TTS error (non-fatal): {tts_error}", exc_info=True)
                    # Continue without TTS - don't block the translation
            
            logger.info(f"Sending translation message with audio_url={translation_msg.get('audio_url') is not None}")
            await self.send_json(translation_msg)
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            await self.send_json({
                'type': 'error',
                'message': f'Translation failed: {str(e)}'
            })

    async def on_speech_start(self):
        """Handle speech start event"""
        await self.send_json({'type': 'speech_start'})

    async def on_speech_stop(self):
        """Handle speech stop event"""
        await self.send_json({'type': 'speech_stop'})

    async def on_error(self, error):
        """Handle ASR error"""
        await self.send_json({
            'type': 'error',
            'message': str(error)
        })

    async def send_json(self, data):
        """Send JSON message to client"""
        try:
            await self.send(text_data=json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
