"""
REST API Views for Emoji Generator

Endpoints:
- POST /detect-face/: Detect face in portrait image
- POST /create-task/: Create video generation task
- GET /task-status/<task_id>/: Check task status
- POST /generate/: Complete generation flow (detect + generate)
- GET /templates/: Get available emoji templates
- POST /upload-image/: Upload local image and get accessible URL
"""

import os
import uuid
import logging
from pathlib import Path
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .services import EmojiService

logger = logging.getLogger(__name__)


def get_emoji_service():
    """Get EmojiService instance with error handling."""
    try:
        return EmojiService()
    except ValueError as e:
        return None, str(e)


@api_view(['GET'])
def get_templates(request):
    """
    Get available emoji templates.
    
    Returns list of templates with id, name, and category.
    """
    templates = EmojiService.get_available_templates()
    categories = EmojiService.get_templates_by_category()
    
    return Response({
        'templates': templates,
        'categories': categories,
        'total': len(templates)
    })


@api_view(['POST'])
def detect_face(request):
    """
    Detect face in a portrait image.
    
    Request body:
        - image_url (required): Public URL of the image
        
    Returns:
        - bbox_face: Face bounding box [x1, y1, x2, y2]
        - ext_bbox_face: Extended expression area [x1, y1, x2, y2]
    """
    image_url = request.data.get('image_url')
    
    if not image_url:
        return Response(
            {'error': 'image_url is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = EmojiService()
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    result = service.detect_face(image_url)
    
    if result.success:
        return Response({
            'success': True,
            'bbox_face': result.bbox_face,
            'ext_bbox_face': result.ext_bbox_face,
            'request_id': result.request_id
        })
    else:
        return Response({
            'success': False,
            'error_code': result.error_code,
            'error_message': result.error_message,
            'request_id': result.request_id
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_task(request):
    """
    Create an async video generation task.
    
    Request body:
        - image_url (required): Public URL of the image
        - face_bbox (required): Face bounding box [x1, y1, x2, y2]
        - ext_bbox (required): Extended expression area [x1, y1, x2, y2]
        - driven_id (optional): Template ID, defaults to "mengwa_kaixin"
        
    Returns:
        - task_id: ID for polling task status
        - task_status: Initial status (usually PENDING)
    """
    image_url = request.data.get('image_url')
    face_bbox = request.data.get('face_bbox')
    ext_bbox = request.data.get('ext_bbox')
    driven_id = request.data.get('driven_id', 'mengwa_kaixin')
    
    # Validate required fields
    if not all([image_url, face_bbox, ext_bbox]):
        return Response(
            {'error': 'image_url, face_bbox, and ext_bbox are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = EmojiService()
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    result = service.create_video_task(
        image_url=image_url,
        face_bbox=face_bbox,
        ext_bbox=ext_bbox,
        driven_id=driven_id
    )
    
    if result.success:
        return Response({
            'success': True,
            'task_id': result.task_id,
            'task_status': result.task_status,
            'request_id': result.request_id
        })
    else:
        return Response({
            'success': False,
            'error_code': result.error_code,
            'error_message': result.error_message,
            'request_id': result.request_id
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def task_status(request, task_id):
    """
    Check the status of a video generation task.
    
    Path parameters:
        - task_id: Task ID from create_task
        
    Returns:
        - task_status: PENDING, RUNNING, SUCCEEDED, FAILED, CANCELED, UNKNOWN
        - video_url: Video URL when status is SUCCEEDED (valid for 24 hours)
        - video_duration: Duration in seconds when completed
    """
    if not task_id:
        return Response(
            {'error': 'task_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = EmojiService()
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    result = service.check_task_status(task_id)
    
    response_data = {
        'task_id': result.task_id,
        'task_status': result.task_status,
        'request_id': result.request_id
    }
    
    if result.task_status == 'SUCCEEDED':
        response_data['success'] = True
        response_data['video_url'] = result.video_url
        response_data['video_duration'] = result.video_duration
    elif result.task_status in ['FAILED', 'CANCELED']:
        response_data['success'] = False
        response_data['error_code'] = result.error_code
        response_data['error_message'] = result.error_message
    else:
        # PENDING, RUNNING
        response_data['success'] = None  # In progress
    
    return Response(response_data)


@api_view(['POST'])
def generate_emoji(request):
    """
    Complete emoji generation flow (detect face + create task).
    
    This is a convenience endpoint that combines face detection and task creation.
    After calling this, poll the task-status endpoint for completion.
    
    Request body:
        - image_url (required): Public URL of the image
        - driven_id (optional): Template ID, defaults to "mengwa_kaixin"
        
    Returns:
        - task_id: ID for polling task status
        - bbox_face: Detected face bounding box
        - ext_bbox_face: Detected expression area
    """
    image_url = request.data.get('image_url')
    driven_id = request.data.get('driven_id', 'mengwa_kaixin')
    
    if not image_url:
        return Response(
            {'error': 'image_url is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = EmojiService()
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Step 1: Detect face
    logger.info(f"Starting emoji generation for image: {image_url[:50]}...")
    detection = service.detect_face(image_url)
    
    if not detection.success:
        return Response({
            'success': False,
            'step': 'face_detection',
            'error_code': detection.error_code,
            'error_message': detection.error_message,
            'request_id': detection.request_id
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Step 2: Create video task
    video_result = service.create_video_task(
        image_url=image_url,
        face_bbox=detection.bbox_face,
        ext_bbox=detection.ext_bbox_face,
        driven_id=driven_id
    )
    
    if not video_result.success:
        return Response({
            'success': False,
            'step': 'video_task_creation',
            'error_code': video_result.error_code,
            'error_message': video_result.error_message,
            'request_id': video_result.request_id
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'task_id': video_result.task_id,
        'task_status': video_result.task_status,
        'bbox_face': detection.bbox_face,
        'ext_bbox_face': detection.ext_bbox_face,
        'driven_id': driven_id,
        'message': 'Task created. Poll /task-status/<task_id>/ for completion.'
    })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint for emoji generator service."""
    try:
        service = EmojiService()
        api_configured = True
    except ValueError:
        api_configured = False
    
    return Response({
        'status': 'ok',
        'service': 'emoji_generator',
        'api_key_configured': api_configured,
        'templates_count': len(EmojiService.get_available_templates())
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """
    Upload a local image file and get an accessible URL.
    
    Request:
        - file: Image file (multipart/form-data)
        
    Returns:
        - success: Boolean
        - image_url: Accessible URL for the uploaded image
        - filename: The saved filename
        
    Note: 
        This creates a publicly accessible URL for the image.
        In production, consider using a CDN or cloud storage with signed URLs.
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided. Use "file" as the field name.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = request.FILES['file']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp']
    if uploaded_file.content_type not in allowed_types:
        return Response(
            {
                'error': f'Invalid file type: {uploaded_file.content_type}. Allowed: JPEG, PNG, WebP, BMP',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        return Response(
            {'error': 'File too large. Maximum size is 10MB.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.MEDIA_ROOT) / 'emoji_uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        ext = Path(uploaded_file.name).suffix.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
            ext = '.jpg'  # Default extension
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Save the file locally first
        file_path = upload_dir / unique_filename
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        logger.info(f"Image saved locally: {unique_filename}")
        
        # Upload to DashScope temporary storage to get a public URL
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        if not api_key:
            raise Exception("DASHSCOPE_API_KEY not configured")
        
        # Use DashScope file upload API
        dashscope_url = upload_to_dashscope(str(file_path), api_key)
        
        if dashscope_url:
            # Build local preview URL that the browser can display
            preview_url = request.build_absolute_uri(
                f"{settings.MEDIA_URL}emoji_uploads/{unique_filename}"
            )
            
            logger.info(f"Image uploaded to DashScope: {dashscope_url[:60]}...")
            return Response({
                'success': True,
                'image_url': dashscope_url,      # oss:// URL for API calls
                'preview_url': preview_url,       # Local URL for browser preview
                'filename': unique_filename,
                'size': uploaded_file.size,
                'content_type': uploaded_file.content_type,
            })
        else:
            raise Exception("Failed to get URL from DashScope")
        
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        return Response(
            {'error': f'Failed to save file: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def upload_to_dashscope(file_path: str, api_key: str) -> str:
    """
    Upload a file to DashScope temporary storage and get a public URL.
    
    The URL is valid for 48 hours.
    Uses the official DashScope SDK's OssUtils for reliable uploads.
    
    Args:
        file_path: Local file path
        api_key: DashScope API key
        
    Returns:
        Public oss:// URL for the uploaded file, or None if failed
    """
    try:
        from dashscope.utils.oss_utils import OssUtils
        
        # Upload the file using DashScope's OSS utility directly
        # This returns an oss:// URL that's accessible by DashScope services
        oss_url, _ = OssUtils.upload(
            model="emoji-v1",
            file_path=file_path,
            api_key=api_key
        )
        
        if oss_url:
            logger.info(f"File uploaded to DashScope OSS: {oss_url[:80] if len(oss_url) > 80 else oss_url}")
            return oss_url
        else:
            logger.error("OssUtils.upload returned None")
            return None
            
    except Exception as e:
        logger.error(f"DashScope OSS upload error: {e}")
        import traceback
        traceback.print_exc()
        return None


@api_view(['GET'])
def download_video(request):
    """
    Proxy endpoint to download video from Aliyun CDN.
    
    This solves CORS issues and ensures proper filename with .mp4 extension.
    
    Query params:
        - url: The video URL from Aliyun
        - filename: Optional filename (will have .mp4 appended if missing)
    """
    video_url = request.GET.get('url')
    filename = request.GET.get('filename', f'emoji_{int(__import__("time").time())}.mp4')
    
    if not video_url:
        return Response(
            {'error': 'url parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Ensure filename has .mp4 extension
    if not filename.endswith('.mp4'):
        filename = filename + '.mp4'
    
    try:
        import requests
        from django.http import StreamingHttpResponse
        
        # Fetch the video from Aliyun
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Create streaming response
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        http_response = StreamingHttpResponse(
            generate(),
            content_type='video/mp4'
        )
        http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        http_response['Content-Length'] = response.headers.get('Content-Length', '')
        
        return http_response
        
    except Exception as e:
        logger.error(f"Video download proxy error: {e}")
        return Response(
            {'error': f'Failed to download video: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
