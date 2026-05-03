from rest_framework import serializers
from .models import Question, KnowledgePoint, ChatNote

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id',
            'course_id',
            'topic',
            'question_type',
            'difficulty',
            'question_text',
            'options',
            'answer',
            'explanation',
            'source_files',
            'source_chapter',
            'source_excerpt',
            'generation_context',
            'created_at',
        ]


class ChatNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatNote
        fields = '__all__'


class KnowledgePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgePoint
        fields = [
            'id',
            'course_id',
            'topic',
            'sequence',
            'title',
            'definition',
            'details',
            'importance',
            'source_excerpt',
            'source_chapter',
            'translations',
            'created_at',
        ]
