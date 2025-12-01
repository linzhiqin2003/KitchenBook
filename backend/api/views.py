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
import re
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
        # 移除各种可能的工具调用标记
        patterns = [
            r'<\s*\|?\s*DSML\s*\|?\s*[^>]*>.*?</\s*\|?\s*DSML\s*\|?\s*[^>]*>',  # DSML 标签
            r'<\s*\|?\s*DSML\s*\|?\s*[^>]*>',  # 单独的 DSML 开始标签
            r'</\s*\|?\s*DSML\s*\|?\s*[^>]*>',  # 单独的 DSML 结束标签
            r'<function_calls?>.*?</function_calls?>',  # function_calls 标签
            r'<invoke[^>]*>.*?</invoke>',  # invoke 标签
            r'<\|.*?\|>',  # 特殊标记 <|...|>
        ]
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
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
                "description": "将菜品添加到用户的购物车。当用户说想要某道菜、点这个、加入购物车时调用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe_id": {
                            "type": "integer",
                            "description": "要添加的菜品ID"
                        },
                        "recipe_name": {
                            "type": "string",
                            "description": "菜品名称，用于确认"
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

你的能力（通过系统内置工具实现，会自动调用）：
1. 查看菜单并推荐菜品
2. 介绍菜品详情
3. 帮顾客添加菜品到购物车
4. 查看购物车内容
5. 帮顾客下单

工作流程：
- 当用户想点菜时，获取菜单后推荐合适的菜品
- 推荐时要热情地描述菜品特色，引导用户点餐
- 用户确认想要某道菜后，添加到购物车
- 下单前确认购物车内容
- 下单时需要询问顾客姓名

你的性格：
- 热情友好，像专业服务员
- 善于推荐，会根据口味偏好给建议
- 回答简洁，适当使用 emoji
- 主动引导点餐流程

重要规则：
- 只推荐菜单上有的菜品
- 如果用户问无关问题，礼貌引导回点餐话题
- 添加购物车和下单都需要用户明确确认
- 绝对不要在回复中输出任何XML标签、代码块或技术内容
- 直接用自然语言回复用户"""
    
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
                        model="deepseek-chat",
                        messages=full_messages,
                        tools=self.TOOLS,
                        tool_choice="auto",
                        max_tokens=1000,
                        temperature=0.7
                    )
                    
                    assistant_message = response.choices[0].message
                    
                    # 没有工具调用，流式输出最终回复
                    if not assistant_message.tool_calls:
                        # 发送思维链完成
                        if thinking_steps:
                            yield f"data: {json.dumps({'type': 'thinking_done', 'steps': thinking_steps}, ensure_ascii=False)}\n\n"
                        
                        # 流式输出最终内容
                        final_stream = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=full_messages,
                            stream=True,
                            max_tokens=500,
                            temperature=0.7
                        )
                        
                        for chunk in final_stream:
                            if chunk.choices[0].delta.content:
                                yield f"data: {json.dumps({'type': 'content', 'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
                        
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
                    model="deepseek-chat",
                    messages=full_messages,
                    stream=True,
                    max_tokens=500,
                    temperature=0.7
                )
                
                for chunk in final_stream:
                    if chunk.choices[0].delta.content:
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
                
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


# ==================== DeepSeek V3.2 Speciale 思考模型 ====================

class DeepSeekSpecialeView(APIView):
    """DeepSeek V3.2 Speciale 思考模型 - 流式输出思维链"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """处理对话请求（流式响应 + 思维链展示）"""
        messages = request.data.get('messages', [])
        
        if not messages:
            return Response({'error': '消息不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        deepseek_speciale_api_key = getattr(settings, 'DEEPSEEK_SPECIALE_API_KEY', None) or settings.DEEPSEEK_API_KEY
        deepseek_speciale_base_url = getattr(settings, 'DEEPSEEK_SPECIALE_BASE_URL', None) or 'https://api.deepseek.com/v3.2_speciale_expires_on_20251215'
        
        if not deepseek_speciale_api_key:
            return Response({
                'error': 'AI 服务未配置，请联系管理员'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 构建消息
        full_messages = messages
        
        def generate():
            """流式生成器"""
            from openai import OpenAI
            
            client = OpenAI(
                api_key=deepseek_speciale_api_key,
                base_url=deepseek_speciale_base_url
            )
            
            try:
                # 发送初始状态
                yield f"data: {json.dumps({'type': 'status', 'content': '正在连接 DeepSeek V3.2 Speciale...'}, ensure_ascii=False)}\n\n"
                
                # 调用 DeepSeek V3.2 Speciale (思考模型，流式)
                response = client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=full_messages,
                    stream=True
                )
                
                current_reasoning = ""
                current_content = ""
                reasoning_started = False
                content_started = False
                
                for chunk in response:
                    # 检查是否有有效的 choices
                    if not chunk.choices:
                        continue
                    
                    delta = chunk.choices[0].delta
                    
                    # 处理思维链 (reasoning_content)
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        reasoning_chunk = delta.reasoning_content
                        current_reasoning += reasoning_chunk
                        if not reasoning_started:
                            reasoning_started = True
                            yield f"data: {json.dumps({'type': 'reasoning_start'}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_chunk}, ensure_ascii=False)}\n\n"
                    
                    # 处理最终内容 (content)
                    if hasattr(delta, 'content') and delta.content:
                        content_chunk = delta.content
                        current_content += content_chunk
                        if not content_started:
                            content_started = True
                            # 标记思维链结束
                            if reasoning_started:
                                yield f"data: {json.dumps({'type': 'reasoning_end'}, ensure_ascii=False)}\n\n"
                            yield f"data: {json.dumps({'type': 'content_start'}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'content', 'content': content_chunk}, ensure_ascii=False)}\n\n"
                
                # 如果有思维链但没有内容，也要发送结束信号
                if reasoning_started and not content_started:
                    yield f"data: {json.dumps({'type': 'reasoning_end'}, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'type': 'done', 'reasoning_length': len(current_reasoning), 'content_length': len(current_content)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
        
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
        import requests
        import base64
        
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
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                error_msg = response.json().get('error', {}).get('message', '请求失败')
                return Response({
                    'error': f'OCR 识别失败: {error_msg}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            result = response.json()
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
            
        except requests.exceptions.Timeout:
            return Response({
                'error': 'OCR 服务响应超时，请稍后重试'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'OCR 处理失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 语音转录 (Groq Whisper via OpenAI SDK) ====================

class WhisperTranscribeView(APIView):
    """语音转录 - 使用 Groq Whisper API 将语音转换为文字（通过 OpenAI SDK 调用）"""
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """处理语音转录请求"""
        from openai import OpenAI
        import tempfile
        import os
        
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
                
                # 使用 OpenAI SDK 调用 Groq API（Groq 兼容 OpenAI API）
                client = OpenAI(
                    api_key=groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                
                # 调用 Whisper API（不使用 prompt 以减少幻觉）
                with open(tmp_file_path, 'rb') as f:
                    transcription = client.audio.transcriptions.create(
                        file=f,
                        model="whisper-large-v3",
                        response_format="text",
                        language="zh",
                        temperature=0.0
                    )
                
                # 返回转录结果
                text = transcription if isinstance(transcription, str) else str(transcription)
                text = text.strip()
                
                # 过滤 Whisper 常见幻觉输出（空录音时容易产生）
                hallucination_keywords = [
                    '字幕', '志愿者', '订阅', '感谢观看', '谢谢观看', '谢谢收看',
                    '翻译', '校对', '审核', '字幕组', '制作', '出品',
                    'subscribe', 'thank you', 'thanks for watching',
                    '请订阅', '点赞', '关注', '三连'
                ]
                text_lower = text.lower()
                
                # 如果转录结果很短且包含幻觉关键词，认为是幻觉
                if len(text) < 30:
                    for keyword in hallucination_keywords:
                        if keyword in text_lower:
                            return Response({
                                'success': True,
                                'text': ''  # 返回空
                            })
                
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
