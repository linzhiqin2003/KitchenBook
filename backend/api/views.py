from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.http import StreamingHttpResponse
import hashlib
import time
import json
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


# ==================== AI 对话助手 ====================

class AiChatView(APIView):
    """AI 对话助手 - 使用 DeepSeek API"""
    authentication_classes = []
    permission_classes = []
    
    def get_menu_context(self):
        """获取当前菜单作为上下文"""
        recipes = Recipe.objects.filter(is_public=True)
        menu_items = []
        for recipe in recipes:
            item = f"- {recipe.title}"
            if recipe.description:
                item += f"：{recipe.description[:50]}"
            if recipe.cooking_time:
                item += f"（烹饪时间约 {recipe.cooking_time} 分钟）"
            menu_items.append(item)
        return "\n".join(menu_items) if menu_items else "暂无菜品"
    
    def get_system_prompt(self):
        """构建系统提示词"""
        menu = self.get_menu_context()
        return f"""你是"LZQ的私人厨房"的 AI 小助手，名叫"小厨"。你的任务是帮助顾客了解菜品、推荐美食、回答关于烹饪的问题。

当前菜单：
{menu}

你的性格特点：
- 热情友好，像一个专业的服务员
- 对美食充满热爱，会用生动的语言描述菜品
- 会根据顾客的口味偏好推荐合适的菜品
- 回答简洁明了，一般不超过 100 字

注意事项：
- 只推荐菜单上有的菜品
- 如果顾客问的问题与美食/餐厅无关，礼貌地引导回美食话题
- 使用轻松友好的语气，可以适当使用 emoji"""
    
    def post(self, request):
        """处理对话请求（流式响应）"""
        messages = request.data.get('messages', [])
        
        if not messages:
            return Response({'error': '消息不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查 API 配置
        if not settings.DEEPSEEK_API_KEY:
            return Response({
                'error': 'AI 服务未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 构建完整的消息列表（加入系统提示）
        full_messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + messages
        
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )
            
            # 流式请求
            def generate():
                stream = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=full_messages,
                    stream=True,
                    max_tokens=500,
                    temperature=0.7
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        # 发送 SSE 格式数据
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                
                yield "data: [DONE]\n\n"
            
            response = StreamingHttpResponse(
                generate(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
            
        except Exception as e:
            return Response({
                'error': f'AI 服务暂时不可用：{str(e)}'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
