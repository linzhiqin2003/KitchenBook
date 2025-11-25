from django.db import models

class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('g', 'Gram'),
        ('kg', 'Kilogram'),
        ('ml', 'Milliliter'),
        ('l', 'Liter'),
        ('pc', 'Piece'),
    ]
    
    name = models.CharField(max_length=100)
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
