from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet, IngredientViewSet, OrderViewSet, ChefAuthView,
    BlogPostViewSet, TagViewSet, CategoryViewSet, AiAgentView, DeepSeekSpecialeView,
    DeepSeekOCRView, WhisperTranscribeView, PDFExtractView, RecipeStepViewSet,
    RecipeIngredientViewSet, AiLabConversationViewSet, AiLabMessageViewSet,
    AiLabNotificationViewSet, ailab_internal_add_message, ailab_internal_push_notification,
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'recipe-steps', RecipeStepViewSet, basename='recipe-step')
router.register(r'recipe-ingredients', RecipeIngredientViewSet, basename='recipe-ingredient')
router.register(r'blog/posts', BlogPostViewSet, basename='blogpost')
router.register(r'blog/tags', TagViewSet)
router.register(r'blog/categories', CategoryViewSet)
router.register(r'ai/conversations', AiLabConversationViewSet, basename='ai-conversation')
router.register(r'ai/messages', AiLabMessageViewSet, basename='ai-message')
router.register(r'ai/notifications', AiLabNotificationViewSet, basename='ai-notification')

urlpatterns = [
    path('', include(router.urls)),
    path('chef/login/', ChefAuthView.as_view(), name='chef-login'),
    path('ai/chat/', AiAgentView.as_view(), name='ai-chat'),
    path('ai/speciale/', DeepSeekSpecialeView.as_view(), name='ai-speciale'),
    path('ai/ocr/', DeepSeekOCRView.as_view(), name='ai-ocr'),
    path('ai/pdf-extract/', PDFExtractView.as_view(), name='ai-pdf-extract'),
    path('ai/transcribe/', WhisperTranscribeView.as_view(), name='ai-transcribe'),
    # 内部端点：Hermes 在客户端断开后的回写通道（token 认证，绕过 JWT）
    path('ai/conversations/<int:pk>/messages/internal/', ailab_internal_add_message, name='ai-conversation-messages-internal'),
    # MyAgent 通知推送：Hermes / cron 用 token 推一条通知到用户收件箱
    path('ai/notifications/internal/', ailab_internal_push_notification, name='ai-notification-internal'),
    path('tarot/', include('cards.urls')),
    path('tarot/', include('readings.urls')),
    path('tarot/', include('oracle.urls')),
]
