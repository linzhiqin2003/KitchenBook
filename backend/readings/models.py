from django.db import models
from cards.models import TarotCard

class Spread(models.Model):
    """Pre-defined tarot spread types with position configurations."""
    name = models.CharField(max_length=100, unique=True)
    name_cn = models.CharField(max_length=100)  # Chinese name
    description = models.TextField()
    card_count = models.IntegerField()
    positions = models.JSONField()  # List of position names
    layout = models.JSONField(default=list)  # Grid layout hints for frontend
    
    def __str__(self):
        return f"{self.name} ({self.card_count} cards)"

class Reading(models.Model):
    session_key = models.CharField(max_length=255, blank=True, null=True)
    question = models.TextField()
    spread = models.ForeignKey(Spread, on_delete=models.SET_NULL, null=True, blank=True)
    spread_type = models.CharField(max_length=50)  # Fallback
    created_at = models.DateTimeField(auto_now_add=True)
    ai_interpretation = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.spread_type} - {self.created_at}"

class ReadingCard(models.Model):
    reading = models.ForeignKey(Reading, related_name='cards', on_delete=models.CASCADE)
    card = models.ForeignKey(TarotCard, on_delete=models.CASCADE)
    position_index = models.IntegerField()
    position_name = models.CharField(max_length=100)
    is_reversed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['position_index']

