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
