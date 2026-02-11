"""
REST API Views for Interpretation App
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from common.config import get_settings, SUPPORTED_LANGUAGES
from .services.translation_service import TranslationService

# File ASR imports
import os
import uuid
import logging
from pathlib import Path
from django.conf import settings as django_settings
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .services.file_asr_service import FileASRService
from .services.transcribe_translate_service import transcribe_and_translate, transcribe_and_translate_stream, generate_minutes_stream, refine_and_translate

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    settings = get_settings()
    api_key_set = bool(settings.api.dashscope_api_key)
    return Response({
        'status': 'ok',
        'api_key_configured': api_key_set,
    })


@api_view(['GET'])
def get_config(request):
    """Get application configuration"""
    settings = get_settings()
    return Response({
        'supported_languages': SUPPORTED_LANGUAGES,
        'default_source_lang': 'en',
        'default_target_lang': settings.translation.target_lang,
    })


@api_view(['GET'])
def get_languages(request):
    """Get supported languages"""
    # Format for frontend select options
    languages = [
        {'code': code, 'name': info['name'], 'english': info['english']}
        for code, info in SUPPORTED_LANGUAGES.items()
    ]
    return Response({'languages': languages})


@api_view(['POST'])
def translate_text(request):
    """Translate text using configured translation provider"""
    text = request.data.get('text', '')
    source_lang = request.data.get('source_lang', 'auto')
    target_lang = request.data.get('target_lang', 'Chinese')
    
    if not text:
        return Response(
            {'error': 'Text is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = TranslationService(
            source_lang=source_lang,
            target_lang=target_lang
        )
        result = service.translate(text, source_lang, target_lang)
        
        return Response({
            'original': result.original_text,
            'translated': result.translated_text,
            'source_lang': result.source_lang,
            'target_lang': result.target_lang,
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_tts_voices(request):
    """Get available TTS voices"""
    from common.providers.dashscope_tts import QWEN_TTS_VOICES
    
    voices = [
        {
            'id': voice_id,
            'gender': info['gender'],
            'style': info['style'],
            'description': info['description'],
            'emoji': info.get('emoji', '🔊'),
        }
        for voice_id, info in QWEN_TTS_VOICES.items()
    ]
    
    return Response({'voices': voices})


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def submit_file_asr(request):
    """
    Upload audio file and submit for ASR transcription (Fun-ASR).
    
    Request:
        - file: Audio file
        - model: 'fun-asr' (default) or 'fun-asr-mtl'
        
    Returns:
        - success: Boolean
        - task_id: Task ID
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    uploaded_file = request.FILES['file']
    settings_obj = get_settings()
    model_name = request.data.get('model') or settings_obj.api.dashscope_file_asr_model
    
    # Basic validation
    # Fun-ASR supports: aac, amr, avi, flac, flv, m4a, mkv, mov, mp3, mp4, mpeg, ogg, opus, wav, webm, wma, wmv
    # We'll just check extension mostly, validation handled by server/sdk eventually
    ext = Path(uploaded_file.name).suffix.lower()
    
    try:
        # 1. Save locally first (temporarily)
        upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
                
        logger.info(f"ASR file saved locally: {file_path}")
        
        # 3. Submit Task (Directly to Groq via Service)
        # Use Groq model from request or settings
        target_model = request.data.get('model') or settings_obj.api.groq_asr_model
        
        result = FileASRService.transcribe(
            file_path=str(file_path),
            model=target_model
        )
        
        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Submit ASR error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_asr_result(request):
    """
    Check ASR task status.
    
    Query:
        - task_id: Task ID
    """
    try:
        task_id = request.GET.get('task_id')
        if not task_id:
            return Response({'error': 'task_id required'}, status=status.HTTP_400_BAD_REQUEST)
            
        result = FileASRService.get_task_result(task_id)
        return Response(result)
    except Exception as e:
        logger.error(f"Get ASR result error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def submit_file_translation(request):
    """
    Upload audio file and submit for translation to English (Groq).
    
    Request:
        - file: Audio file
        - model: Groq whisper model (default: whisper-large-v3)
        
    Returns:
        - success: Boolean
        - task_id: Task ID
        - task_type: 'translation'
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    uploaded_file = request.FILES['file']
    settings_obj = get_settings()
    
    # Groq supports: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
    ext = Path(uploaded_file.name).suffix.lower()
    
    try:
        # 1. Save locally first
        upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
                
        logger.info(f"Translation file saved locally: {file_path}")
        
        # 2. Submit Task (Groq Translation API)
        target_model = request.data.get('model') or settings_obj.api.groq_asr_model
        
        result = FileASRService.translate(
            file_path=str(file_path),
            model=target_model
        )
        
        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Submit translation error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def transcribe_translate(request):
    """
    Upload audio → ASR transcription → Cerebras translation.

    POST /api/interpretation/transcribe-translate/
      - file: audio file (webm, mp3, wav, etc.)
      - source_lang: e.g. 'en', 'zh'
      - target_lang: e.g. 'Chinese', 'English'
      - asr_tier: 'free' (default) or 'premium' (DashScope, requires JWT + credits)

    Auth: Optional JWT for free tier, required JWT for premium tier.
    Returns: { transcription, translation, source_lang, target_lang, balance_seconds? }
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    asr_tier = request.data.get('asr_tier', 'free')

    # Try optional JWT authentication
    user_groq_key = None
    authenticated_user = None
    from rest_framework_simplejwt.authentication import JWTAuthentication
    try:
        auth_result = JWTAuthentication().authenticate(request)
        if auth_result:
            authenticated_user, _ = auth_result
            if asr_tier == 'free':
                profile = getattr(authenticated_user, 'profile', None)
                if profile and profile.groq_api_key:
                    user_groq_key = profile.groq_api_key
                # If no user key, fall through to server key
    except Exception:
        # No JWT or invalid JWT → fall through to server key
        pass

    # Premium tier requires authentication
    if asr_tier == 'premium' and authenticated_user is None:
        return Response(
            {'error': 'Authentication required for premium ASR'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    uploaded_file = request.FILES['file']
    source_lang = request.data.get('source_lang', 'en')
    target_lang = request.data.get('target_lang', 'Chinese')

    ext = Path(uploaded_file.name).suffix.lower() or '.webm'
    upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{uuid.uuid4().hex}{ext}"
    try:
        with open(file_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        # Premium tier: check credits before processing
        if asr_tier == 'premium':
            from credits.services import get_balance, get_audio_duration, deduct_for_audio, InsufficientCreditsError
            import math
            duration = get_audio_duration(str(file_path))
            required = math.ceil(duration)
            balance = get_balance(authenticated_user)
            if balance < required:
                return Response(
                    {
                        'error': 'Insufficient credits',
                        'balance_seconds': balance,
                        'required_seconds': required,
                    },
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

        from apps.interpretation.services.transcribe_translate_service import (
            GroqAllRateLimitedError, GroqKeyInvalidError,
        )

        # Transcribe with user's key; key pool auto-rotates on 429
        try:
            result = transcribe_and_translate(
                str(file_path), source_lang, target_lang,
                groq_api_key=user_groq_key,
                asr_tier=asr_tier,
            )
        except GroqKeyInvalidError:
            if authenticated_user and user_groq_key:
                profile = getattr(authenticated_user, 'profile', None)
                if profile:
                    profile.groq_api_key = ""
                    profile.save(update_fields=["groq_api_key"])
                    logger.warning("Revoked invalid Groq key for user=%s", authenticated_user.pk)
            return Response(
                {'error': 'Your Groq API Key is invalid or revoked. Please update it in Settings.', 'key_revoked': True},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Premium tier: deduct credits after successful ASR
        if asr_tier == 'premium':
            try:
                deduct_for_audio(authenticated_user, duration)
                result['balance_seconds'] = get_balance(authenticated_user)
            except InsufficientCreditsError:
                # Shouldn't happen since we checked above, but handle gracefully
                result['balance_seconds'] = get_balance(authenticated_user)

        return Response(result)

    except Exception as e:
        from apps.interpretation.services.transcribe_translate_service import GroqAllRateLimitedError as _RLE
        if isinstance(e, _RLE):
            logger.warning("transcribe_translate rate-limited (all keys exhausted): %s", e)
            return Response(
                {'error': 'Rate limited, please slow down', 'retry_after': 5},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        logger.error(f"transcribe_translate error: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if file_path.exists():
            file_path.unlink()


@api_view(['POST'])
def refine_transcription(request):
    """
    Refine ASR transcription with Cerebras LLM, then translate.

    POST /api/interpretation/refine/
      - text: transcription text to refine
      - source_lang: e.g. 'en', 'zh'
      - target_lang: e.g. 'Chinese', 'English'

    Returns: { refined_transcription, translation, source_lang, target_lang }
    """
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'No text provided'}, status=status.HTTP_400_BAD_REQUEST)

    source_lang = request.data.get('source_lang', 'en')
    target_lang = request.data.get('target_lang', 'Chinese')

    try:
        result = refine_and_translate(text, source_lang, target_lang)
        return Response(result)
    except Exception as e:
        logger.error(f"refine_transcription error: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def gen_title(request):
    """
    POST /api/interpretation/generate-title/
      - text: transcription or translation text
    Returns: { title }
    """
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'No text provided'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        from .services.transcribe_translate_service import generate_title
        title = generate_title(text)
        return Response({'title': title})
    except Exception as e:
        logger.error(f"gen_title error: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def transcribe_translate_stream(request):
    """
    POST → StreamingHttpResponse (NDJSON line-by-line).
    Yields transcription first, then translation, for progressive display.
    """
    if 'file' not in request.FILES:
        import json
        return StreamingHttpResponse(
            iter([json.dumps({"event": "error", "text": "No file provided"}) + "\n"]),
            content_type='application/x-ndjson',
            status=400,
        )

    uploaded_file = request.FILES['file']
    source_lang = request.POST.get('source_lang', 'en')
    target_lang = request.POST.get('target_lang', 'Chinese')

    ext = Path(uploaded_file.name).suffix.lower() or '.webm'
    upload_dir = Path(django_settings.MEDIA_ROOT) / 'asr_uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{uuid.uuid4().hex}{ext}"
    with open(file_path, 'wb+') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)

    def event_stream():
        import json
        try:
            for line in transcribe_and_translate_stream(str(file_path), source_lang, target_lang):
                yield line
        except Exception as e:
            logger.error(f"transcribe_translate_stream error: {e}", exc_info=True)
            yield json.dumps({"event": "error", "text": str(e)}) + "\n"
        finally:
            if file_path.exists():
                file_path.unlink()

    return StreamingHttpResponse(
        event_stream(),
        content_type='application/x-ndjson',
    )


@csrf_exempt
@require_POST
def generate_meeting_minutes(request):
    """
    POST JSON { "entries": [{ "original": "...", "translated": "..." }] }
    → StreamingHttpResponse (NDJSON): {"event":"chunk","text":"..."} then {"event":"done"}
    """
    import json as json_mod
    try:
        body = json_mod.loads(request.body)
    except (json_mod.JSONDecodeError, ValueError):
        return StreamingHttpResponse(
            iter([json_mod.dumps({"event": "error", "text": "Invalid JSON"}) + "\n"]),
            content_type='application/x-ndjson',
            status=400,
        )

    entries = body.get("entries", [])
    if not entries:
        return StreamingHttpResponse(
            iter([json_mod.dumps({"event": "error", "text": "No entries provided"}) + "\n"]),
            content_type='application/x-ndjson',
            status=400,
        )

    return StreamingHttpResponse(
        generate_minutes_stream(entries),
        content_type='application/x-ndjson',
    )
