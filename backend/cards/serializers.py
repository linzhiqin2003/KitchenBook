from rest_framework import serializers
from .models import TarotCard

class TarotCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarotCard
        fields = '__all__'
