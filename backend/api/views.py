from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
import hashlib
import time
from .models import Recipe, Ingredient, Order, BlogPost, Tag
from .serializers import (
    RecipeSerializer, PublicRecipeSerializer, IngredientSerializer, OrderSerializer,
    BlogPostListSerializer, BlogPostDetailSerializer, TagSerializer
)


class ChefAuthView(APIView):
    """厨师登录验证"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        
        if username == settings.CHEF_USERNAME and password == settings.CHEF_PASSWORD:
            # 生成一个简单的 token（基于密钥和时间戳）
            token_data = f"{settings.SECRET_KEY}:{username}:{int(time.time())}"
            token = hashlib.sha256(token_data.encode()).hexdigest()[:32]
            
            return Response({
                'success': True,
                'token': token,
                'message': '登录成功，欢迎回来主厨！'
            })
        else:
            return Response({
                'success': False,
                'message': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    def get(self, request):
        """验证 token 是否有效（简单验证：只要有 token 就认为有效）"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token and len(token) == 32:
            return Response({'valid': True})
        return Response({'valid': False}, status=status.HTTP_401_UNAUTHORIZED)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    authentication_classes = [] # Disable SessionAuth to avoid CSRF in this demo
    permission_classes = []
    
    def get_serializer_class(self):
        if self.action == 'list':
            # Check if 'full' param is present (for chef view)
            if self.request.query_params.get('mode') == 'chef':
                return RecipeSerializer
            return PublicRecipeSerializer
        
        # For single item retrieve
        if self.action == 'retrieve':
             # Only chef needs full details (steps/ingredients)
             if self.request.query_params.get('mode') == 'chef':
                 return RecipeSerializer
             return PublicRecipeSerializer
             
        return RecipeSerializer

    def get_queryset(self):
        # Filter non-public recipes from guest view
        if self.request.query_params.get('mode') != 'chef':
            return Recipe.objects.filter(is_public=True)
        return Recipe.objects.all()

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    authentication_classes = []
    permission_classes = []

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    authentication_classes = []
    permission_classes = []


# ==================== 技术博客视图 ====================

class TagViewSet(viewsets.ModelViewSet):
    """标签管理"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    authentication_classes = []
    permission_classes = []


class BlogPostViewSet(viewsets.ModelViewSet):
    """博客文章管理"""
    authentication_classes = []
    permission_classes = []
    
    def get_queryset(self):
        queryset = BlogPost.objects.all()
        
        # 访客模式只显示已发布的文章
        if self.request.query_params.get('mode') != 'chef':
            queryset = queryset.filter(is_published=True)
        
        # 按标签筛选
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        # 只看精选
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(content__icontains=search)
        
        return queryset.distinct().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BlogPostListSerializer
        return BlogPostDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 增加阅读计数（访客模式）
        if request.query_params.get('mode') != 'chef':
            instance.view_count += 1
            instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        # 如果设置为发布，记录发布时间
        if serializer.validated_data.get('is_published') and not serializer.validated_data.get('published_at'):
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        # 如果首次发布，记录发布时间
        instance = self.get_object()
        if serializer.validated_data.get('is_published') and not instance.published_at:
            serializer.save(published_at=timezone.now())
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取博客统计信息"""
        total_posts = BlogPost.objects.filter(is_published=True).count()
        total_views = BlogPost.objects.filter(is_published=True).aggregate(
            total=Sum('view_count')
        )['total'] or 0
        total_tags = Tag.objects.count()
        
        return Response({
            'total_posts': total_posts,
            'total_views': total_views,
            'total_tags': total_tags
        })
    
    @action(detail=False, methods=['get'], url_path='by-slug/(?P<slug>[^/.]+)')
    def by_slug(self, request, slug=None):
        """通过 slug 获取文章"""
        try:
            # 访客模式只能访问已发布的文章
            if request.query_params.get('mode') != 'chef':
                post = BlogPost.objects.get(slug=slug, is_published=True)
            else:
                post = BlogPost.objects.get(slug=slug)
            
            # 增加阅读计数（访客模式）
            if request.query_params.get('mode') != 'chef':
                post.view_count += 1
                post.save(update_fields=['view_count'])
            
            serializer = BlogPostDetailSerializer(post)
            return Response(serializer.data)
        except BlogPost.DoesNotExist:
            return Response({'error': '文章不存在'}, status=status.HTTP_404_NOT_FOUND)
