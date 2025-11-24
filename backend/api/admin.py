from django.contrib import admin
from .models import Recipe, RecipeStep, Ingredient, RecipeIngredient, Order, OrderItem

class RecipeStepInline(admin.StackedInline):
    model = RecipeStep
    extra = 1

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'cooking_time', 'category')
    inlines = [RecipeIngredientInline, RecipeStepInline]

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit', 'in_stock')
    list_filter = ('unit',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
