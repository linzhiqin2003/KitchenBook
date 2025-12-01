from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, IngredientViewSet, OrderViewSet, ChefAuthView, BlogPostViewSet, TagViewSet, AiChatView

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'blog/posts', BlogPostViewSet, basename='blogpost')
router.register(r'blog/tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('chef/login/', ChefAuthView.as_view(), name='chef-login'),
    path('ai/chat/', AiChatView.as_view(), name='ai-chat'),
]

