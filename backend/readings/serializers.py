from rest_framework import serializers
from .models import Spread, Reading, ReadingCard

class SpreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spread
        fields = '__all__'

class ReadingCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingCard
        fields = '__all__'

class ReadingSerializer(serializers.ModelSerializer):
    cards = ReadingCardSerializer(many=True, read_only=True)
    
    class Meta:
        model = Reading
        fields = '__all__'
