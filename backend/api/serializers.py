from rest_framework import serializers
from .models import Recipe, RecipeStep, Ingredient, RecipeIngredient, Order, OrderItem, BlogPost, Tag, AiLabConversation, AiLabMessage

class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ['id', 'recipe', 'step_number', 'description', 'image']
        extra_kwargs = {
            'recipe': {'required': False}  # 在创建时可以从URL获取
        }


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """用于创建/更新食材关联"""
    ingredient_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'recipe', 'ingredient', 'ingredient_name', 'amount', 'quantity_display']
        extra_kwargs = {
            'recipe': {'required': False},
            'ingredient': {'required': False},
            'amount': {'required': False, 'default': 0}
        }
    
    def create(self, validated_data):
        # 如果提供了ingredient_name但没有ingredient，创建或查找食材
        ingredient_name = validated_data.pop('ingredient_name', None)
        if ingredient_name and not validated_data.get('ingredient'):
            ingredient, created = Ingredient.objects.get_or_create(
                name=ingredient_name,
                defaults={'quantity': 0, 'unit': 'g'}
            )
            validated_data['ingredient'] = ingredient
        return super().create(validated_data)

class IngredientSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'category', 'category_display', 'quantity', 'unit', 'threshold', 'in_stock', 'is_low_stock']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    in_stock = serializers.BooleanField(source='ingredient.in_stock', read_only=True)
    quantity = serializers.CharField(source='quantity_display')
    
    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'ingredient_name', 'quantity', 'in_stock']

class PublicRecipeSerializer(serializers.ModelSerializer):
    """For guest view - hides steps and precise ingredients"""
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'cover_image', 'description', 'cooking_time', 'category']

class RecipeSerializer(serializers.ModelSerializer):
    """Full detail for Chef"""
    steps = RecipeStepSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'cover_image', 'description', 'cooking_time', 'category', 'steps', 'ingredients', 'chef_notes', 'is_public']

class OrderItemSerializer(serializers.ModelSerializer):
    recipe_title = serializers.CharField(source='recipe.title', read_only=True)
    recipe_details = RecipeSerializer(source='recipe', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'recipe', 'recipe_title', 'quantity', 'note', 'recipe_details']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'created_at', 'status', 'items']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


# ==================== 技术博客序列化器 ====================

class TagSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'post_count']
    
    def get_post_count(self, obj):
        return obj.posts.filter(is_published=True).count()


class BlogPostListSerializer(serializers.ModelSerializer):
    """博客列表视图 - 简化版"""
    tags = TagSerializer(many=True, read_only=True)
    reading_time = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'summary', 'cover_image', 'tags', 
                  'is_featured', 'view_count', 'created_at', 'published_at', 'reading_time']
    
    def get_reading_time(self, obj):
        # 估算阅读时间（中文约 400 字/分钟）
        word_count = len(obj.content)
        minutes = max(1, round(word_count / 400))
        return minutes


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """博客详情视图 - 完整版"""
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), 
        many=True, 
        write_only=True,
        source='tags',
        required=False
    )
    reading_time = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'summary', 'content', 'cover_image', 
                  'tags', 'tag_ids', 'is_published', 'is_featured', 'view_count',
                  'created_at', 'updated_at', 'published_at', 'reading_time']
        read_only_fields = ['slug', 'view_count', 'created_at', 'updated_at']
    
    def get_reading_time(self, obj):
        word_count = len(obj.content)
        minutes = max(1, round(word_count / 400))
        return minutes
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = BlogPost.objects.create(**validated_data)
        post.tags.set(tags)
        return post
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


# ==================== AI Lab 序列化器 ====================

class AiLabMessageSerializer(serializers.ModelSerializer):
    """AI Lab 消息序列化器"""
    class Meta:
        model = AiLabMessage
        fields = ['id', 'conversation', 'role', 'content', 'reasoning', 'sub_turns', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'conversation': {'required': False}
        }


class AiLabConversationListSerializer(serializers.ModelSerializer):
    """AI Lab 会话列表序列化器"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AiLabConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count', 'last_message']

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'role': last_msg.role,
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content
            }
        return None


class AiLabConversationDetailSerializer(serializers.ModelSerializer):
    """AI Lab 会话详情序列化器（含消息）"""
    messages = AiLabMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AiLabConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']
