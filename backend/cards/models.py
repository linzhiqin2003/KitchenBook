from django.db import models

class Suit(models.TextChoices):
    WANDS = 'Wands', 'Wands'
    CUPS = 'Cups', 'Cups'
    SWORDS = 'Swords', 'Swords'
    PENTACLES = 'Pentacles', 'Pentacles'
    NONE = 'None', 'None'

class Arcana(models.TextChoices):
    MAJOR = 'Major', 'Major'
    MINOR = 'Minor', 'Minor'

class TarotCard(models.Model):
    name = models.CharField(max_length=100, unique=True)
    number = models.IntegerField()
    arcana = models.CharField(max_length=10, choices=Arcana.choices)
    suit = models.CharField(max_length=10, choices=Suit.choices, default=Suit.NONE)
    img = models.CharField(max_length=100)  # filename like "m00.jpg"
    
    # Using JSONField for lists of strings
    fortune_telling = models.JSONField(default=list) 
    keywords = models.JSONField(default=list)
    meanings_light = models.JSONField(default=list)
    meanings_shadow = models.JSONField(default=list)
    
    def __str__(self):
        return self.name
