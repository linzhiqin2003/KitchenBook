from rest_framework import serializers
from .models import Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id',
            'course_id',
            'topic',
            'difficulty',
            'question_text',
            'options',
            'answer',
            'explanation',
            'source_files',
            'created_at',
        ]
