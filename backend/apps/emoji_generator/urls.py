"""
URL Configuration for Emoji Generator App

API Endpoints:
- GET  /health/              - Health check
- GET  /templates/           - Get available emoji templates  
- POST /detect-face/         - Detect face in image
- POST /create-task/         - Create video generation task
- GET  /task-status/<id>/    - Check task status
- POST /generate/            - Complete flow (detect + create task)
- POST /upload-image/        - Upload local image file
"""

from django.urls import path
from . import views

app_name = 'emoji_generator'

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('templates/', views.get_templates, name='templates'),
    path('detect-face/', views.detect_face, name='detect-face'),
    path('create-task/', views.create_task, name='create-task'),
    path('task-status/<str:task_id>/', views.task_status, name='task-status'),
    path('generate/', views.generate_emoji, name='generate'),
    path('upload-image/', views.upload_image, name='upload-image'),
    path('download-video/', views.download_video, name='download-video'),
]
