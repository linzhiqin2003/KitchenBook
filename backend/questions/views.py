from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Question
from .serializers import QuestionSerializer
from .services.generator import generate_question, batch_generate as batch_generate_service
from .services.parser import parse_simulation_questions, parse_courseware


class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for questions.
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """
        Generate a single question from a provided seed or random seed.
        POST /api/questions/generate/
        Body: {"seed": "optional seed question text"}
        """
        seed = request.data.get('seed')
        
        if not seed:
            # Use a random seed from simulation questions
            seeds = parse_simulation_questions()
            if not seeds:
                return Response(
                    {"error": "No seed questions available"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            import random
            seed = random.choice(seeds)
        
        result = generate_question(seed)
        
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Save to database
        question = Question.objects.create(
            topic=result.get('topic', 'general'),
            question_text=result.get('question', ''),
            options=result.get('options', []),
            answer=result.get('answer', ''),
            explanation=result.get('explanation', ''),
            seed_question=seed
        )
        
        serializer = self.get_serializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='batch-generate')
    def batch_generate(self, request):
        """
        Generate multiple questions from all seeds.
        POST /api/questions/batch-generate/
        Body: {"limit": 5}  # optional limit
        """
        limit = request.data.get('limit', 5)
        
        results = batch_generate_service(limit=limit)
        
        created_questions = []
        for result in results:
            if "error" not in result:
                question = Question.objects.create(
                    topic=result.get('topic', 'general'),
                    question_text=result.get('question', ''),
                    options=result.get('options', []),
                    answer=result.get('answer', ''),
                    explanation=result.get('explanation', ''),
                    seed_question=result.get('seed_question', '')
                )
                created_questions.append(question)
        
        serializer = self.get_serializer(created_questions, many=True)
        return Response({
            "generated": len(created_questions),
            "questions": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='topics')
    def topics(self, request):
        """
        Get available topics from courseware.
        GET /api/questions/topics/
        """
        context = parse_courseware()
        return Response({"topics": list(context.keys())})

