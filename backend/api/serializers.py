from rest_framework import serializers
from .models import Recipe, RecipeStep, Ingredient, RecipeIngredient, Order, OrderItem

class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ['id', 'step_number', 'description', 'image']

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'quantity', 'unit', 'threshold', 'in_stock', 'is_low_stock']

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
