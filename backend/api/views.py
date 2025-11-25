from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django.conf import settings
import hashlib
import time
from .models import Recipe, Ingredient, Order
from .serializers import RecipeSerializer, PublicRecipeSerializer, IngredientSerializer, OrderSerializer


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
