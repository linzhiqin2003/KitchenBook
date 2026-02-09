from django.db import models

class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('g', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Milliliter'),
        ('l', 'Liter'),
        ('pc', 'Piece'),
    ]
    
    CATEGORY_CHOICES = [
        ('meat', '肉类'),
        ('seafood', '海鲜'),
        ('vegetable', '蔬菜'),
        ('seasoning', '调味料'),
        ('staple', '主食/干货'),
        ('dairy', '乳制品'),
        ('other', '其他'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', help_text="食材分类")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Current stock quantity")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='g')
    threshold = models.DecimalField(max_digits=10, decimal_places=2, default=10, help_text="Low stock alert threshold")
    
    @property
    def in_stock(self):
        return self.quantity > 0
        
    @property
    def is_low_stock(self):
        return self.quantity <= self.threshold
    
    def __str__(self):
        return f"{self.name} ({self.quantity}{self.unit})"

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    cover_image = models.ImageField(upload_to='recipes/', null=True, blank=True)
    description = models.TextField(blank=True, help_text="Public description for the menu")
    cooking_time = models.IntegerField(help_text="Minutes")
    category = models.CharField(max_length=100, blank=True)
    
    # Chef only fields
    is_public = models.BooleanField(default=True, help_text="Show on guest menu")
    chef_notes = models.TextField(blank=True, help_text="Private notes for the chef")
    
    def __str__(self):
        return self.title

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ingredients', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name='used_in', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount required per serving")
    # quantity field kept for backward compatibility display, but logic should use amount
    quantity_display = models.CharField(max_length=50, help_text="Display text e.g. '200g'", blank=True)
    
    def __str__(self):
        return f"{self.ingredient.name} for {self.recipe.title}"

class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='steps', on_delete=models.CASCADE)
    step_number = models.PositiveIntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='steps/', null=True, blank=True)
    
    class Meta:
        ordering = ['step_number']
    
    def __str__(self):
        return f"Step {self.step_number} of {self.recipe.title}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cooking', 'Cooking'),
        ('completed', 'Completed'),
    ]
    
    customer_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"Order by {self.customer_name} at {self.created_at}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    note = models.CharField(max_length=200, blank=True, help_text="Customer special request")
    
    def __str__(self):
        return f"{self.quantity}x {self.recipe.title}"


# ==================== 技术博客模块 ====================

class Tag(models.Model):
    """博客标签"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#10b981', help_text="Hex color code")
    
    def __str__(self):
        return self.name


# ==================== AI Lab 会话模块 ====================

class AiLabConversation(models.Model):
    """AI Lab 会话"""
    title = models.CharField(max_length=200, default="新对话")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class AiLabMessage(models.Model):
    """AI Lab 消息"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    conversation = models.ForeignKey(
        AiLabConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    reasoning = models.TextField(blank=True, null=True, help_text="AI 思维链内容")
    sub_turns = models.JSONField(blank=True, null=True, help_text="工具调用时间线 [{reasoning, toolCall}]")
    model_name = models.CharField(max_length=50, blank=True, null=True, help_text="使用的模型名称")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# ==================== 技术博客模块 ====================

class BlogPost(models.Model):
    """技术博客文章"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.TextField(max_length=500, help_text="文章摘要", blank=True)
    content = models.TextField(help_text="Markdown 格式内容")
    cover_image = models.ImageField(upload_to='blog/', null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    
    # 元数据
    is_published = models.BooleanField(default=False, help_text="是否发布")
    is_featured = models.BooleanField(default=False, help_text="是否精选")
    view_count = models.PositiveIntegerField(default=0)
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # 自动生成 slug
        if not self.slug:
            from django.utils.text import slugify
            import time
            base_slug = slugify(self.title, allow_unicode=True)
            if not base_slug:
                base_slug = f"post-{int(time.time())}"
            self.slug = base_slug
        super().save(*args, **kwargs)
