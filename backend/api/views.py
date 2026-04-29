# API Views for KitchenBook
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.http import StreamingHttpResponse
from django.core.files.storage import default_storage
import hashlib
import time
import json
import re
import os
import uuid
import base64
import tempfile
from .models import Recipe, Ingredient, Order, BlogPost, Tag, Category, RecipeStep, RecipeIngredient
from .serializers import (
    RecipeSerializer, PublicRecipeSerializer, IngredientSerializer, OrderSerializer,
    BlogPostListSerializer, BlogPostDetailSerializer, TagSerializer, CategorySerializer,
    RecipeStepSerializer, RecipeIngredientSerializer, RecipeIngredientWriteSerializer
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


class RecipeStepViewSet(viewsets.ModelViewSet):
    """菜谱步骤管理"""
    serializer_class = RecipeStepSerializer
    authentication_classes = []
    permission_classes = []
    
    def get_queryset(self):
        recipe_id = self.request.query_params.get('recipe')
        if recipe_id:
            return RecipeStep.objects.filter(recipe_id=recipe_id).order_by('step_number')
        return RecipeStep.objects.all().order_by('recipe_id', 'step_number')
    
    def perform_create(self, serializer):
        recipe_id = self.request.data.get('recipe')
        if recipe_id:
            serializer.save(recipe_id=recipe_id)
        else:
            serializer.save()
    
    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request):
        """批量更新步骤 - 一次性替换某菜谱的所有步骤"""
        recipe_id = request.data.get('recipe_id')
        steps_data = request.data.get('steps', [])
        
        if not recipe_id:
            return Response({'error': '请提供菜谱ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': '菜谱不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取现有步骤
        existing_steps = {step.id: step for step in recipe.steps.all()}
        updated_ids = set()
        
        for step_data in steps_data:
            step_id = step_data.get('id')
            
            if step_id and step_id in existing_steps:
                # 更新现有步骤
                step = existing_steps[step_id]
                step.step_number = step_data.get('step_number', step.step_number)
                step.description = step_data.get('description', step.description)
                # 图片单独处理（通过单独的API上传）
                step.save()
                updated_ids.add(step_id)
            else:
                # 创建新步骤
                new_step = RecipeStep.objects.create(
                    recipe=recipe,
                    step_number=step_data.get('step_number', 1),
                    description=step_data.get('description', '')
                )
                updated_ids.add(new_step.id)
        
        # 删除不在更新列表中的步骤
        for step_id, step in existing_steps.items():
            if step_id not in updated_ids:
                step.delete()
        
        # 返回更新后的步骤列表
        updated_steps = RecipeStep.objects.filter(recipe=recipe).order_by('step_number')
        serializer = RecipeStepSerializer(updated_steps, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        """为步骤上传图片"""
        step = self.get_object()
        image = request.FILES.get('image')
        if not image:
            return Response({'error': '请上传图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        step.image = image
        step.save()
        return Response(RecipeStepSerializer(step).data)


class RecipeIngredientViewSet(viewsets.ModelViewSet):
    """菜谱食材关联管理"""
    authentication_classes = []
    permission_classes = []
    
    def get_queryset(self):
        recipe_id = self.request.query_params.get('recipe')
        if recipe_id:
            return RecipeIngredient.objects.filter(recipe_id=recipe_id)
        return RecipeIngredient.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'batch_update']:
            return RecipeIngredientWriteSerializer
        return RecipeIngredientSerializer
    
    def perform_create(self, serializer):
        recipe_id = self.request.data.get('recipe')
        if recipe_id:
            serializer.save(recipe_id=recipe_id)
        else:
            serializer.save()
    
    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request):
        """批量更新食材 - 一次性替换某菜谱的所有食材"""
        recipe_id = request.data.get('recipe_id')
        ingredients_data = request.data.get('ingredients', [])
        
        if not recipe_id:
            return Response({'error': '请提供菜谱ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': '菜谱不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 删除现有食材关联
        recipe.ingredients.all().delete()
        
        # 创建新的食材关联
        for ing_data in ingredients_data:
            ingredient_name = ing_data.get('ingredient_name', '')
            quantity_display = ing_data.get('quantity_display', '')
            
            if ingredient_name:
                # 查找或创建食材
                ingredient, _ = Ingredient.objects.get_or_create(
                    name=ingredient_name,
                    defaults={'quantity': 0, 'unit': 'g'}
                )
                
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ing_data.get('amount', 0),
                    quantity_display=quantity_display
                )
        
        # 返回更新后的食材列表
        updated_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
        serializer = RecipeIngredientSerializer(updated_ingredients, many=True)
        return Response(serializer.data)


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


class CategoryViewSet(viewsets.ModelViewSet):
    """博客分类（文件夹）管理"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = []
    permission_classes = []


class BlogPostViewSet(viewsets.ModelViewSet):
    """博客文章管理"""
    authentication_classes = []
    permission_classes = []
    
    def get_queryset(self):
        queryset = BlogPost.objects.all()
        
        # 对于更新/删除/获取单个对象的操作，不限制 is_published
        # 这样厨师可以编辑草稿文章
        if self.action in ['update', 'partial_update', 'destroy', 'retrieve']:
            # 如果是 chef 模式或者是修改操作，返回所有文章
            if self.request.query_params.get('mode') == 'chef':
                pass  # 不过滤
            elif self.action in ['update', 'partial_update', 'destroy']:
                pass  # 修改和删除操作不过滤
            elif self.action == 'retrieve' and self.request.query_params.get('mode') != 'chef':
                # 访客获取单篇文章时，只能看已发布的
                queryset = queryset.filter(is_published=True)
        elif self.action == 'list':
            # 列表页：访客模式只显示已发布的文章
            if self.request.query_params.get('mode') != 'chef':
                queryset = queryset.filter(is_published=True)
        
        # 按分类筛选
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

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
    
    @action(detail=False, methods=['get'])
    def graph(self, request):
        """知识图谱数据：返回 nodes + edges"""
        import re as _re
        queryset = BlogPost.objects.filter(is_published=True)
        category_slug = request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        posts = list(queryset)
        slug_to_id = {p.slug: p.id for p in posts}

        nodes = []
        edges_set = set()

        for p in posts:
            nodes.append({
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'summary': p.summary[:120] if p.summary else '',
                'reading_time': max(1, round(len(p.content) / 400)),
                'view_count': p.view_count,
            })

            # 从 content 中提取内链 /blog/{slug}
            for match in _re.finditer(r'\(/blog/([^)]+)\)', p.content):
                target_slug = match.group(1)
                # URL decode
                from urllib.parse import unquote
                target_slug = unquote(target_slug)
                if target_slug in slug_to_id and slug_to_id[target_slug] != p.id:
                    edges_set.add((p.id, slug_to_id[target_slug]))

            # 手动关联的 related_posts
            for related in p.related_posts.filter(is_published=True):
                if related.id in {n['id'] for n in nodes} or related.id in slug_to_id.values():
                    edges_set.add((p.id, related.id))

        edges = [{'source': s, 'target': t} for s, t in edges_set]

        return Response({'nodes': nodes, 'edges': edges})

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
    
    @action(detail=False, methods=['post'], url_path='upload-image')
    def upload_image(self, request):
        """上传博客内容图片"""
        if 'image' not in request.FILES:
            return Response({'error': '请选择图片文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        image_file = request.FILES['image']
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return Response({'error': '不支持的图片格式'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件大小 (限制 5MB)
        if image_file.size > 5 * 1024 * 1024:
            return Response({'error': '图片大小不能超过 5MB'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成唯一文件名
        ext = os.path.splitext(image_file.name)[1].lower()
        filename = f"blog_content/{uuid.uuid4().hex}{ext}"
        
        # 保存文件
        path = default_storage.save(filename, image_file)
        
        # 返回图片 URL
        url = request.build_absolute_uri(settings.MEDIA_URL + path)
        
        return Response({
            'success': True,
            'url': url,
            'markdown': f'![image]({url})'
        })
# ==================== AI 智能体助手 ====================

class AiAgentView(APIView):
    """AI 智能体助手 - 支持工具调用，可以推荐菜品、操作购物车、下单"""
    authentication_classes = []
    permission_classes = []
    
    @staticmethod
    def clean_ai_response(text):
        """清理 AI 回复中可能出现的工具调用标记"""
        if not text:
            return text
        
        # 移除各种可能的工具调用标记（按优先级排序）
        patterns = [
            # 1. 匹配 < | DSML | xxx> 格式的完整块（带空格和竖线的变体）
            r'<\s*\|[^>]*>[\s\S]*?<\s*/\s*\|[^>]*>',
            # 2. 匹配 <|xxx|> 或 </|xxx|> 单独标签
            r'<\s*/?\s*\|[^>]*>',
            # 3. 完整的 DSML 块
            r'<\s*DSML[^>]*>[\s\S]*?<\s*/\s*DSML[^>]*>',
            r'<\s*/?\s*DSML[^>]*>',
            # 4. 完整的 function_calls 块
            r'<\s*function_calls?\s*>[\s\S]*?<\s*/\s*function_calls?\s*>',
            r'<\s*/?\s*function_calls?\s*>',
            # 5. 完整的 invoke 块
            r'<\s*invoke[^>]*>[\s\S]*?<\s*/\s*invoke\s*>',
            r'<\s*/?\s*invoke[^>]*>',
            # 6. 完整的 antml 块（Claude 特有）
            r'<\s*antml[^>]*>[\s\S]*?<\s*/\s*antml[^>]*>',
            r'<\s*/?\s*antml[^>]*>',
            # 7. 完整的 tool_call 块
            r'<\s*tool_call[^>]*>[\s\S]*?<\s*/\s*tool_call\s*>',
            r'<\s*/?\s*tool_call[^>]*>',
            # 8. parameter 标签
            r'<\s*/?\s*parameter[^>]*>',
            # 9. 特殊标记 <|...|>
            r'<\|[^|]*\|>',
            # 10. name="..." 或 string="..." 参数残留
            r'\b(name|string)\s*=\s*["\'][^"\']*["\']',
            # 11. JSON 代码块残留
            r'```json[\s\S]*?```',
            # 12. 孤立的数字行（可能是参数残留如 "21" "1"）
            r'^\s*\d+\s*$',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
        
        # 清理多余空行和空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'^\s*\n', '', text)  # 清理开头空行
        return text.strip()
    
    # 定义可用工具
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_menu",
                "description": "获取餐厅的菜单列表，可按分类筛选。当用户询问有什么菜、想看菜单、或需要推荐时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "菜品分类，可选值：烧烤、小炒、水煮、麻辣烫、小吃、主食、西餐、菜、大菜、奶茶。不传则返回全部菜品。"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_recipe_detail",
                "description": "获取某道菜的详细信息，包括描述、烹饪时间、食材等。当用户想了解某道菜的详情时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe_id": {
                            "type": "integer",
                            "description": "菜品ID"
                        },
                        "recipe_name": {
                            "type": "string",
                            "description": "菜品名称，如果不知道ID可以用名称搜索"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_to_cart",
                "description": "将菜品添加到购物车。【重要】只有当用户明确说出菜品名称要点某道菜时才能调用！禁止自作主张添加用户没有明确要求的菜品。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe_id": {
                            "type": "integer",
                            "description": "要添加的菜品ID"
                        },
                        "recipe_name": {
                            "type": "string",
                            "description": "菜品名称，必须是用户明确提到的"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "数量，默认为1",
                            "default": 1
                        },
                        "note": {
                            "type": "string",
                            "description": "备注，如：不要辣、多加葱等"
                        }
                    },
                    "required": ["recipe_id", "recipe_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_cart",
                "description": "查看用户当前购物车中的菜品。当用户问购物车有什么、想看看点了什么时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "place_order",
                "description": "提交订单。当用户确认要下单、结账、提交订单时调用。需要顾客姓名。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "顾客姓名，用于取餐"
                        }
                    },
                    "required": ["customer_name"]
                }
            }
        }
    ]
    
    def get_system_prompt(self):
        """构建系统提示词"""
        return """你是"LZQ的私人厨房"的 AI 点餐助手，名叫"小厨"。

## 核心原则（必须遵守）
1. **你不知道任何菜品信息！** 必须通过工具查询真实菜单。
2. **只能添加用户明确要求的菜品！** 
   - 用户说"我要甜品" → 先查询菜单，列出选项让用户选择
   - 用户说"黄油饼干奶冻来一份" → 可以添加
   - 用户说"这两个都要" → 只添加之前提到的那两个
   - **绝对禁止自作主张添加用户没提到的菜品！**

## 可用工具
1. get_menu(category) - 查看菜单，category 可选：烧烤/小炒/甜点/主食/小吃 等
2. get_recipe_detail(recipe_id/recipe_name) - 查看菜品详情
3. add_to_cart(recipe_id, recipe_name) - 添加到购物车
4. view_cart() - 查看购物车
5. place_order(customer_name) - 提交订单

## 必须调用工具的场景
- "有什么菜" / "看看菜单" / "推荐一下" → get_menu()
- "想吃甜品" / "有什么甜点" → get_menu(category="甜点")，然后列出选项让用户选
- "想吃辣的" / "有什么小炒" → get_menu(category="小炒")
- "这道菜怎么样" / "介绍一下XX" → get_recipe_detail()
- "我要XX" / "来一份XX" → add_to_cart(具体菜名)
- "看看购物车" / "点了什么" → view_cart()
- "下单" / "结账" → place_order()

## 添加购物车的严格规则
1. **只添加用户明确说出名字的菜品**
2. 用户说"都要"时，只添加对话中**之前提到过的菜品**
3. 用户说"随便来点"时，先推荐让用户确认，**不要直接添加**
4. **禁止自作主张添加任何用户没有明确要求的菜品**

## 性格
热情友好 🧑‍🍳 | 简洁明了 | 善于推荐 | 使用 emoji

## 绝对禁止
- 编造菜品信息（必须查询后再回答）
- 输出 XML/JSON/代码/工具名称
- 输出 <function_calls>、<invoke> 等技术标记"""
    
    # ===== 工具执行函数 =====
    
    def tool_get_menu(self, category=None):
        """获取菜单"""
        recipes = Recipe.objects.filter(is_public=True)
        if category:
            recipes = recipes.filter(category=category)
        
        menu_items = []
        for r in recipes:
            menu_items.append({
                "id": r.id,
                "name": r.title,
                "description": r.description or "",
                "category": r.category or "其他",
                "cooking_time": r.cooking_time,
                "cover_image": r.cover_image.url if r.cover_image else None
            })
        
        return {
            "success": True,
            "total": len(menu_items),
            "items": menu_items
        }
    
    def tool_get_recipe_detail(self, recipe_id=None, recipe_name=None):
        """获取菜品详情"""
        try:
            if recipe_id:
                recipe = Recipe.objects.get(id=recipe_id, is_public=True)
            elif recipe_name:
                recipe = Recipe.objects.filter(title__icontains=recipe_name, is_public=True).first()
                if not recipe:
                    return {"success": False, "error": f"未找到名为'{recipe_name}'的菜品"}
            else:
                return {"success": False, "error": "请提供菜品ID或名称"}
            
            # 获取食材
            ingredients = []
            for ri in recipe.recipe_ingredients.all():
                ingredients.append({
                    "name": ri.ingredient.name,
                    "amount": ri.quantity_display or f"{ri.amount} {ri.ingredient.unit}"
                })
            
            return {
                "success": True,
                "recipe": {
                    "id": recipe.id,
                    "name": recipe.title,
                    "description": recipe.description or "",
                    "category": recipe.category or "其他",
                    "cooking_time": recipe.cooking_time,
                    "cover_image": recipe.cover_image.url if recipe.cover_image else None,
                    "ingredients": ingredients
                }
            }
        except Recipe.DoesNotExist:
            return {"success": False, "error": "菜品不存在"}
    
    def tool_add_to_cart(self, recipe_id, recipe_name, quantity=1, note=None):
        """添加到购物车 - 返回指令让前端执行"""
        try:
            recipe = Recipe.objects.get(id=recipe_id, is_public=True)
            return {
                "success": True,
                "action": "add_to_cart",
                "data": {
                    "recipe_id": recipe.id,
                    "recipe_name": recipe.title,
                    "quantity": quantity,
                    "note": note or "",
                    "cover_image": recipe.cover_image.url if recipe.cover_image else None
                },
                "message": f"已将 {recipe.title} x{quantity} 加入购物车"
            }
        except Recipe.DoesNotExist:
            return {"success": False, "error": f"菜品 {recipe_name} 不存在"}
    
    def tool_view_cart(self):
        """查看购物车 - 返回指令让前端获取"""
        return {
            "success": True,
            "action": "view_cart",
            "message": "请查看右侧购物车"
        }
    
    def tool_place_order(self, customer_name):
        """下单 - 返回指令让前端执行"""
        return {
            "success": True,
            "action": "place_order",
            "data": {
                "customer_name": customer_name
            },
            "message": f"正在为 {customer_name} 提交订单..."
        }
    
    def execute_tool(self, tool_name, arguments):
        """执行工具调用"""
        tool_map = {
            "get_menu": self.tool_get_menu,
            "get_recipe_detail": self.tool_get_recipe_detail,
            "add_to_cart": self.tool_add_to_cart,
            "view_cart": self.tool_view_cart,
            "place_order": self.tool_place_order
        }
        
        if tool_name in tool_map:
            return tool_map[tool_name](**arguments)
        return {"success": False, "error": f"未知工具: {tool_name}"}
    
    def get_tool_thinking_text(self, tool_name, arguments):
        """根据工具名生成思考文字"""
        thinking_map = {
            "get_menu": "让我看看今天有什么好吃的...",
            "get_recipe_detail": f"查一下这道菜的详细信息...",
            "add_to_cart": f"好的，帮你加入购物车...",
            "view_cart": "看看购物车里有什么...",
            "place_order": "正在提交订单..."
        }
        return thinking_map.get(tool_name, "思考中...")
    
    def post(self, request):
        """处理对话请求（流式响应 + 思维链展示）"""
        messages = request.data.get('messages', [])
        cart_info = request.data.get('cart', [])
        
        if not messages:
            return Response({'error': '消息不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not settings.DEEPSEEK_API_KEY:
            return Response({
                'error': 'AI 服务未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 构建系统提示
        cart_status = ""
        if cart_info:
            cart_items = [f"- {item['name']} x{item['quantity']}" for item in cart_info]
            cart_status = f"\n\n当前购物车：\n" + "\n".join(cart_items)
        else:
            cart_status = "\n\n当前购物车：空"
        
        full_messages = [
            {"role": "system", "content": self.get_system_prompt() + cart_status}
        ] + messages
        
        def generate():
            """流式生成器"""
            from openai import OpenAI
            
            client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )
            
            actions = []
            thinking_steps = []
            
            try:
                # 工具调用循环
                for round_num in range(3):
                    # 发送思考状态
                    if round_num == 0:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': '让我想想...'}, ensure_ascii=False)}\n\n"
                    
                    response = client.chat.completions.create(
                        model="deepseek-v4-flash",
                        messages=full_messages,
                        tools=self.TOOLS,
                        tool_choice="auto",
                        max_tokens=1000,
                        temperature=0.3,  # 降低温度，让模型更倾向于遵循指令调用工具
                        extra_body={"thinking": {"type": "disabled"}},
                    )
                    
                    assistant_message = response.choices[0].message
                    
                    # 没有工具调用，流式输出最终回复
                    if not assistant_message.tool_calls:
                        # 发送思维链完成
                        if thinking_steps:
                            yield f"data: {json.dumps({'type': 'thinking_done', 'steps': thinking_steps}, ensure_ascii=False)}\n\n"
                        
                        # 流式输出最终内容
                        final_stream = client.chat.completions.create(
                            model="deepseek-v4-flash",
                            messages=full_messages,
                            stream=True,
                            max_tokens=500,
                            temperature=0.5,  # 最终回复可以稍微有点创意
                            extra_body={"thinking": {"type": "disabled"}},
                        )
                        
                        content_buffer = ""
                        for chunk in final_stream:
                            if chunk.choices[0].delta.content:
                                content_chunk = chunk.choices[0].delta.content
                                content_buffer += content_chunk
                        
                        # 清理可能泄露的工具调用标记
                        cleaned_content = self.clean_ai_response(content_buffer)
                        if cleaned_content:
                            yield f"data: {json.dumps({'type': 'content', 'content': cleaned_content}, ensure_ascii=False)}\n\n"
                        
                        # 注意：actions 已在工具调用时立即发送，这里不再重复发送
                        yield "data: [DONE]\n\n"
                        return
                    
                    # 处理工具调用
                    full_messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # 执行每个工具调用
                    for tool_call in assistant_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        # 发送工具调用思考状态
                        thinking_text = self.get_tool_thinking_text(func_name, func_args)
                        thinking_steps.append({
                            "tool": func_name,
                            "text": thinking_text,
                            "args": func_args
                        })
                        yield f"data: {json.dumps({'type': 'thinking', 'content': thinking_text, 'tool': func_name}, ensure_ascii=False)}\n\n"
                        
                        # 执行工具
                        result = self.execute_tool(func_name, func_args)
                        
                        # 收集动作
                        if result.get("action"):
                            action_data = {
                                "type": result["action"],
                                "data": result.get("data", {}),
                                "message": result.get("message", "")
                            }
                            actions.append(action_data)
                            # 立即发送动作
                            yield f"data: {json.dumps({'type': 'action', 'action': action_data}, ensure_ascii=False)}\n\n"
                        
                        # 添加工具结果
                        full_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                
                # 循环结束，获取最终响应
                if thinking_steps:
                    yield f"data: {json.dumps({'type': 'thinking_done', 'steps': thinking_steps}, ensure_ascii=False)}\n\n"
                
                final_stream = client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=full_messages,
                    stream=True,
                    max_tokens=500,
                    temperature=0.5,  # 最终回复可以稍微有点创意
                    extra_body={"thinking": {"type": "disabled"}},
                )
                
                # 收集完整内容后再清理输出
                content_buffer = ""
                for chunk in final_stream:
                    if chunk.choices[0].delta.content:
                        content_buffer += chunk.choices[0].delta.content
                
                # 清理可能泄露的工具调用标记
                cleaned_content = self.clean_ai_response(content_buffer)
                if cleaned_content:
                    yield f"data: {json.dumps({'type': 'content', 'content': cleaned_content}, ensure_ascii=False)}\n\n"
                
                # 注意：actions 已在工具调用时立即发送，这里不再重复发送
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
        
        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


# ==================== DeepSeek Reasoner 思考模型 ====================

class DeepSeekSpecialeView(APIView):
    """AI Lab 思考模型 - 支持多模型 + agentic 工具调用循环"""
    authentication_classes = []
    permission_classes = []

    MAX_ROUNDS = 10

    @staticmethod
    def _build_system_prompt():
        from datetime import datetime
        now = datetime.now()
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        time_str = f"{now.strftime('%Y年%m月%d日 %H:%M')} {weekdays[now.weekday()]}"
        return (
            f"当前时间：{time_str}。\n"
            "你是一个乐于助人的 AI 助手。你可以使用工具来获取实时信息或执行计算。\n\n"
            "【重要规则】\n"
            "1. 需要实时信息、最新数据或你不确定的事实时，必须调用 web_search 工具，禁止凭记忆编造。\n"
            "2. [REF:n] 标记只能来自工具返回的结果，禁止自己编造引用标记。\n"
            "3. 引用时将 [REF:n] 放在具体数据或论述旁边，不要把多个引用堆在一起。\n"
            "4. 使用工具后直接给出答案，不要说「让我帮你查找」「稍等」之类的过渡语。\n"
            "5. 如果用户的问题不需要工具（常识、闲聊），直接回答即可。\n"
            "6. 多次搜索时，每次工具返回的 [REF:n] 编号全局唯一递增，请直接使用工具给出的编号，不要重新编号。\n"
            "7. 调用 web_search 时，务必使用 focus 参数传递检索重点，告诉摘要 AI 应该关注提取什么信息。例如搜索公司财报时设置 focus='关注最新季度营收、净利润和同比增长率'。\n"
        )

    # DeepSeek 官方 API（OpenAI 兼容），通过 extra_body.thinking 切换思考模式
    MODEL_CONFIGS = {
        'deepseek-v4-flash': {
            'label': 'DeepSeek V4 Flash',
            'api_key_setting': 'DEEPSEEK_API_KEY',
            'base_url': 'https://api.deepseek.com',
            'model': 'deepseek-v4-flash',
            'extra_body': {},
            'extra_headers': {},
        },
        'deepseek-v4-pro': {
            'label': 'DeepSeek V4 Pro',
            'api_key_setting': 'DEEPSEEK_API_KEY',
            'base_url': 'https://api.deepseek.com',
            'model': 'deepseek-v4-pro',
            'extra_body': {},
            'extra_headers': {},
        },
    }

    VALID_THINKING_LEVELS = {'none', 'low', 'medium', 'high', 'max'}

    def post(self, request):
        """处理对话请求（流式响应 + agentic 工具调用循环）"""
        messages = request.data.get('messages', [])
        model_key = request.data.get('model', 'deepseek-v4-pro')
        thinking_level = request.data.get('thinking', 'low')

        if not messages:
            return Response({'error': '消息不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        if thinking_level not in self.VALID_THINKING_LEVELS:
            thinking_level = 'low'

        # 查找模型配置
        model_config = self.MODEL_CONFIGS.get(model_key)
        if not model_config:
            return Response({'error': f'不支持的模型: {model_key}'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取 API 凭证
        api_key = getattr(settings, model_config['api_key_setting'], '')
        base_url = model_config.get('base_url') or getattr(settings, model_config.get('base_url_setting', ''), '')

        if not api_key:
            return Response({
                'error': f'{model_config["label"]} 服务未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 构建消息 — 前端只发 role + content，不含 reasoning_content
        full_messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ] + messages

        def generate():
            from openai import OpenAI
            from .tools import TOOL_DEFINITIONS, execute_tool_streaming, reset_ref_counter, get_collected_references
            import time as _time

            # 重置引用计数器，确保本次请求内 [REF:n] 编号全局唯一递增
            reset_ref_counter()

            client = OpenAI(api_key=api_key, base_url=base_url)

            extra_body = dict(model_config.get('extra_body') or {})
            if thinking_level == 'none':
                extra_body['thinking'] = {'type': 'disabled'}
            else:
                extra_body['thinking'] = {'type': 'enabled'}
                extra_body['reasoning_effort'] = thinking_level
            extra_headers = model_config.get('extra_headers') or {}
            model_name = model_config['model']

            def emit(data):
                return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            total_reasoning = 0
            total_content = 0

            try:
                for round_num in range(self.MAX_ROUNDS):
                    # ── 1. 调用 API（流式 + 工具） ──
                    create_kwargs = dict(
                        model=model_name,
                        messages=full_messages,
                        tools=TOOL_DEFINITIONS,
                        stream=True,
                    )
                    if extra_body:
                        create_kwargs['extra_body'] = extra_body
                    if extra_headers:
                        create_kwargs['extra_headers'] = extra_headers

                    stream = client.chat.completions.create(**create_kwargs)

                    reasoning_started = False
                    content_started = False
                    current_reasoning = ""
                    current_content = ""

                    # 工具调用累积器: {index: {id, name, arguments}}
                    tool_calls_acc = {}
                    finish_reason = None

                    # ── 2. 处理流式 chunks ──
                    for chunk in stream:
                        if not chunk.choices:
                            continue

                        choice = chunk.choices[0]
                        delta = choice.delta
                        finish_reason = choice.finish_reason or finish_reason

                        # 2a. reasoning（DeepSeek 直连: model_extra.reasoning_content）
                        extra = getattr(delta, 'model_extra', None) or {}
                        rc = extra.get('reasoning_content') or extra.get('reasoning') or getattr(delta, 'reasoning_content', None)
                        if rc:
                            if not reasoning_started:
                                reasoning_started = True
                                yield emit({"type": "reasoning_start"})
                            current_reasoning += rc
                            yield emit({"type": "reasoning", "content": rc})

                        # 2b. tool_calls delta
                        if delta.tool_calls:
                            for tc_delta in delta.tool_calls:
                                idx = tc_delta.index
                                if idx not in tool_calls_acc:
                                    # 结束 reasoning 阶段
                                    if reasoning_started and not content_started:
                                        yield emit({"type": "reasoning_end"})
                                        reasoning_started = False
                                    # 首次出现 — 替换模式
                                    tool_calls_acc[idx] = {
                                        "id": tc_delta.id or "",
                                        "name": (tc_delta.function.name if tc_delta.function else "") or "",
                                        "arguments": (tc_delta.function.arguments if tc_delta.function else "") or "",
                                    }
                                    yield emit({
                                        "type": "tool_call",
                                        "index": idx,
                                        "id": tool_calls_acc[idx]["id"],
                                        "name": tool_calls_acc[idx]["name"],
                                        "arguments": tool_calls_acc[idx]["arguments"],
                                    })
                                else:
                                    # 后续 chunk — 追加 arguments
                                    args_chunk = (tc_delta.function.arguments if tc_delta.function else "") or ""
                                    tool_calls_acc[idx]["arguments"] += args_chunk
                                    # 补全 id/name（有些 API 只在首 chunk 给）
                                    if tc_delta.id:
                                        tool_calls_acc[idx]["id"] = tc_delta.id
                                    if tc_delta.function and tc_delta.function.name:
                                        tool_calls_acc[idx]["name"] = tc_delta.function.name
                                    yield emit({
                                        "type": "tool_call_delta",
                                        "index": idx,
                                        "id": tool_calls_acc[idx]["id"],
                                        "arguments": args_chunk,
                                    })

                        # 2c. content
                        if delta.content:
                            if not content_started:
                                content_started = True
                                if reasoning_started:
                                    yield emit({"type": "reasoning_end"})
                                    reasoning_started = False
                                yield emit({"type": "content_start"})
                            current_content += delta.content
                            yield emit({"type": "content", "content": delta.content})

                    # 收尾 reasoning
                    if reasoning_started and not content_started and not tool_calls_acc:
                        yield emit({"type": "reasoning_end"})

                    total_reasoning += len(current_reasoning)
                    total_content += len(current_content)

                    # ── 3. 判断 finish_reason ──
                    if finish_reason == "tool_calls" and tool_calls_acc:
                        # 构建 assistant 消息（带 tool_calls，content 为 None）
                        assistant_tool_calls = []
                        for idx in sorted(tool_calls_acc.keys()):
                            tc = tool_calls_acc[idx]
                            assistant_tool_calls.append({
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": tc["arguments"],
                                }
                            })

                        full_messages.append({
                            "role": "assistant",
                            "content": None,
                            "reasoning_content": current_reasoning or None,
                            "tool_calls": assistant_tool_calls,
                        })

                        # 执行每个工具
                        for idx in sorted(tool_calls_acc.keys()):
                            tc = tool_calls_acc[idx]
                            tool_id = tc["id"]
                            tool_name = tc["name"]

                            # emit execution_start
                            yield emit({
                                "type": "tool_execution_start",
                                "index": idx,
                                "id": tool_id,
                                "name": tool_name,
                            })

                            # 解析参数
                            try:
                                tool_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                            except json.JSONDecodeError:
                                tool_args = {}

                            t0 = _time.time()
                            result_str, error_str = None, None
                            for tool_event in execute_tool_streaming(tool_name, tool_args):
                                if "progress" in tool_event:
                                    evt = {
                                        "type": "tool_progress",
                                        "index": idx,
                                        "id": tool_id,
                                        "name": tool_name,
                                        "message": tool_event["progress"],
                                    }
                                    if "urls" in tool_event:
                                        evt["urls"] = tool_event["urls"]
                                    yield emit(evt)
                                elif "result" in tool_event:
                                    result_str = tool_event["result"]
                                elif "error" in tool_event:
                                    error_str = tool_event["error"]
                            duration_ms = int((_time.time() - t0) * 1000)

                            if error_str:
                                yield emit({
                                    "type": "tool_execution_error",
                                    "index": idx,
                                    "id": tool_id,
                                    "name": tool_name,
                                    "error": error_str,
                                    "duration_ms": duration_ms,
                                })
                                tool_content = json.dumps({"error": error_str}, ensure_ascii=False)
                            else:
                                yield emit({
                                    "type": "tool_execution_result",
                                    "index": idx,
                                    "id": tool_id,
                                    "name": tool_name,
                                    "result": result_str,
                                    "duration_ms": duration_ms,
                                })
                                tool_content = result_str

                            # 追加 tool 消息到历史
                            full_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": tool_content,
                            })

                        # continue loop — 下一轮会让模型继续思考
                        continue

                    # finish_reason == "stop" 或其他 → 完成
                    break

                # ── 兜底：若模型未生成 content，用最后一轮 reasoning 作为回复 ──
                if total_content == 0 and current_reasoning:
                    fallback = current_reasoning.strip()
                    yield emit({"type": "content_start"})
                    yield emit({"type": "content", "content": fallback})
                    total_content = len(fallback)

                # ── 自动补齐引用来源列表 ──
                collected_refs = get_collected_references()
                if collected_refs:
                    ref_lines = ["\n\n---\n**引用来源**\n"]
                    for ref_id, url, title, domain in collected_refs:
                        safe_title = title.replace('[', '').replace(']', '')
                        ref_lines.append(
                            f"- **{ref_id}.** [{safe_title}]({url})"
                        )
                    ref_block = "\n".join(ref_lines) + "\n"
                    if not content_started:
                        yield emit({"type": "content_start"})
                    yield emit({"type": "content", "content": ref_block})
                    total_content += len(ref_block)

                # ── 发送完成信号 ──
                yield emit({
                    "type": "done",
                    "reasoning_length": total_reasoning,
                    "content_length": total_content,
                })
                yield "data: [DONE]\n\n"

            except Exception as e:
                import traceback
                traceback.print_exc()
                yield emit({"type": "error", "error": str(e)})

        response = StreamingHttpResponse(generate(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


# ==================== DeepSeek-OCR 图片识别 ====================

class DeepSeekOCRView(APIView):
    """DeepSeek-OCR 图片识别 - 通过硅基流动 API 将图片转换为 Markdown"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """处理图片 OCR 请求"""
        # 获取图片数据
        image_file = request.FILES.get('image')
        image_base64 = request.data.get('image_base64')
        
        if not image_file and not image_base64:
            return Response({'error': '请上传图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取 API 密钥
        siliconflow_api_key = getattr(settings, 'SILICONFLOW_API_KEY', '')
        if not siliconflow_api_key:
            return Response({
                'error': 'OCR 服务未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # 处理图片
            if image_file:
                # 从上传的文件读取
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                # 获取 MIME 类型
                content_type = image_file.content_type or 'image/png'
            else:
                # 已经是 base64 格式
                # 检查是否包含 data URL 前缀
                if image_base64.startswith('data:'):
                    # 提取 MIME 类型和 base64 数据
                    parts = image_base64.split(',', 1)
                    if len(parts) == 2:
                        mime_part = parts[0]  # data:image/png;base64
                        image_base64 = parts[1]
                        content_type = mime_part.split(':')[1].split(';')[0] if ':' in mime_part else 'image/png'
                    else:
                        content_type = 'image/png'
                else:
                    content_type = 'image/png'
            
            # 构建图片 URL (data URL 格式)
            image_url = f"data:{content_type};base64,{image_base64}"
            
            # 调用硅基流动 DeepSeek-OCR API
            url = f"{settings.SILICONFLOW_BASE_URL}/chat/completions"
            
            payload = {
                "model": "deepseek-ai/DeepSeek-OCR",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            },
                            {
                                "type": "text",
                                "text": "请将图片中的内容转换为 Markdown 格式，特别注意数学公式要用 LaTeX 格式（行内公式用 $...$，块级公式用 $$...$$）。只输出转换后的内容，不要添加任何解释。"
                            }
                        ]
                    }
                ],
                "max_tokens": 4096
            }
            
            headers = {
                "Authorization": f"Bearer {siliconflow_api_key}",
                "Content-Type": "application/json"
            }
            
            # 使用 urllib 替代 requests
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                try:
                    error_data = json.loads(error_body)
                    error_msg = error_data.get('error', {}).get('message', '请求失败')
                except:
                    error_msg = '请求失败'
                return Response({
                    'error': f'OCR 识别失败: {error_msg}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            ocr_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            if not ocr_text:
                return Response({
                    'error': '未能识别图片内容'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'markdown': ocr_text,
                'usage': result.get('usage', {})
            })
            
        except urllib.error.URLError as e:
            if 'timed out' in str(e):
                return Response({
                    'error': 'OCR 服务响应超时，请稍后重试'
                }, status=status.HTTP_504_GATEWAY_TIMEOUT)
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'OCR 处理失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== PDF 文本提取 ====================

class PDFExtractView(APIView):
    """提取 PDF 文件中的文本内容"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        pdf_file = request.FILES.get('file')
        if not pdf_file:
            return Response({'error': '请上传 PDF 文件'}, status=status.HTTP_400_BAD_REQUEST)

        if not pdf_file.name.lower().endswith('.pdf'):
            return Response({'error': '仅支持 PDF 文件'}, status=status.HTTP_400_BAD_REQUEST)

        if pdf_file.size > 20 * 1024 * 1024:  # 20MB limit
            return Response({'error': 'PDF 文件不能超过 20MB'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import fitz  # PyMuPDF
            pdf_bytes = pdf_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            pages = []
            for i, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    pages.append(f"--- Page {i+1} ---\n{text}")
            doc.close()

            if not pages:
                return Response({'error': 'PDF 中未提取到文本内容'}, status=status.HTTP_400_BAD_REQUEST)

            full_text = "\n\n".join(pages)
            # 截断过长文本（保留前 50000 字符）
            if len(full_text) > 50000:
                full_text = full_text[:50000] + f"\n\n... [截断：原文共 {len(full_text)} 字符，已显示前 50000 字符]"

            return Response({
                'text': full_text,
                'pages': len(pages),
                'filename': pdf_file.name,
                'size': pdf_file.size,
            })
        except ImportError:
            return Response({'error': 'PDF 解析库未安装，请联系管理员'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': f'PDF 解析失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 语音转录 (Groq Whisper via OpenAI SDK) ====================

class WhisperTranscribeView(APIView):
    """语音转录 - 使用 Groq Whisper API 将语音转换为文字（通过 OpenAI SDK 调用）"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """处理语音转录请求"""
        from openai import OpenAI
        
        # 获取音频文件
        audio_file = request.FILES.get('audio')
        
        if not audio_file:
            return Response({'error': '请上传音频文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取 Groq API 密钥
        groq_api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not groq_api_key:
            return Response({
                'error': '语音转录服务未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # 将上传的文件保存为临时文件
            suffix = '.webm'  # 默认 webm 格式
            content_type = audio_file.content_type or ''
            if 'mp3' in content_type:
                suffix = '.mp3'
            elif 'wav' in content_type:
                suffix = '.wav'
            elif 'm4a' in content_type:
                suffix = '.m4a'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                for chunk in audio_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # 检测音频文件大小，过小可能是空录音
                file_size = os.path.getsize(tmp_file_path)
                if file_size < 2000:  # 小于 2KB 认为是空录音
                    return Response({
                        'success': True,
                        'text': ''  # 返回空，不调用 API
                    })
                
                # 获取录音时长（从请求参数获取，单位：秒）
                duration = float(request.data.get('duration', 0))
                
                # 使用 OpenAI SDK 调用 Groq API（Groq 兼容 OpenAI API）
                groq_client = OpenAI(
                    api_key=groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                
                # 调用 Whisper API
                with open(tmp_file_path, 'rb') as f:
                    transcription = groq_client.audio.transcriptions.create(
                        file=f,
                        model="whisper-large-v3",
                        response_format="text",
                        language="zh",
                        temperature=0.0
                    )
                
                # 获取转录结果
                text = transcription if isinstance(transcription, str) else str(transcription)
                text = text.strip()
                
                # 如果录音超过10秒，用语言模型整合优化转录结果
                if duration > 10 and text and len(text) > 20:
                    try:
                        deepseek_client = OpenAI(
                            api_key=settings.DEEPSEEK_API_KEY,
                            base_url=settings.DEEPSEEK_BASE_URL
                        )
                        
                        completion = deepseek_client.chat.completions.create(
                            model="deepseek-v4-flash",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "你是一个语音转文字的后处理助手。用户会给你一段语音转录的原始文本，可能有一些重复、口语化或不连贯的地方。请帮助整理成通顺的文字，保持原意不变，不要添加或删除实质内容。直接输出整理后的文字，不要任何解释。"
                                },
                                {
                                    "role": "user",
                                    "content": f"请整理这段语音转录文本：\n\n{text}"
                                }
                            ],
                            max_tokens=500,
                            temperature=0.3,
                            extra_body={"thinking": {"type": "disabled"}},
                        )

                        refined_text = completion.choices[0].message.content.strip()
                        if refined_text:
                            text = refined_text
                    except Exception as e:
                        # 语言模型整合失败，使用原始转录结果
                        print(f"语音整合失败: {e}")
                
                return Response({
                    'success': True,
                    'text': text
                })
                
            finally:
                # 清理临时文件
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'语音转录失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== AI Lab 会话管理 ====================

from .models import AiLabConversation, AiLabMessage
from .serializers import (
    AiLabConversationListSerializer, AiLabConversationDetailSerializer, AiLabMessageSerializer
)


class AiLabConversationViewSet(viewsets.ModelViewSet):
    """AI Lab 会话管理 — 严格按登录用户隔离"""
    queryset = AiLabConversation.objects.all()
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework.permissions import IsAuthenticated
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AiLabConversation.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return AiLabConversationListSerializer
        return AiLabConversationDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='messages')
    def add_message(self, request, pk=None):
        """向会话添加消息"""
        conversation = self.get_object()
        serializer = AiLabMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(conversation=conversation)
            # 更新会话时间
            conversation.save()  # 触发 auto_now

            # 如果是用户消息且会话标题是默认的，则自动更新标题
            if serializer.validated_data.get('role') == 'user' and conversation.title == '新对话':
                content = serializer.validated_data.get('content', '')
                # 取前30个字符作为标题
                new_title = content[:30] + ('...' if len(content) > 30 else '')
                conversation.title = new_title
                conversation.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='token-usage')
    def update_token_usage(self, request, pk=None):
        """更新会话的 token 用量"""
        conversation = self.get_object()
        conversation.token_usage = request.data
        conversation.save(update_fields=['token_usage'])
        return Response(conversation.token_usage)


class AiLabMessageViewSet(viewsets.ModelViewSet):
    """AI Lab 消息管理 — 仅允许操作自己会话下的消息"""
    queryset = AiLabMessage.objects.all()
    serializer_class = AiLabMessageSerializer
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework.permissions import IsAuthenticated
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AiLabMessage.objects.filter(conversation__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """删除消息及其后续所有消息"""
        message = self.get_object()
        conversation = message.conversation

        # 删除该消息及其后的所有消息
        AiLabMessage.objects.filter(
            conversation=conversation,
            created_at__gte=message.created_at
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        """编辑消息，同时删除后续消息"""
        message = self.get_object()
        conversation = message.conversation

        # 删除该消息后的所有消息（不包括自己）
        AiLabMessage.objects.filter(
            conversation=conversation,
            created_at__gt=message.created_at
        ).delete()

        # 更新消息内容
        return super().update(request, *args, **kwargs)
