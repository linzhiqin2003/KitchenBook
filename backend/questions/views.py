from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Question
from .serializers import QuestionSerializer
from .services.generator import generate_question, batch_generate as batch_generate_service
from .services.parser import parse_simulation_questions, parse_courseware
import random


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

    @action(detail=False, methods=['post'], url_path='random-cached')
    def random_cached(self, request):
        """
        Get a random cached question from database that the user hasn't seen.
        POST /api/questiongen/questions/random-cached/
        Body: {"seen_ids": [1, 2, 3]}  # IDs of questions user has already seen
        """
        seen_ids = request.data.get('seen_ids', [])
        
        # Get questions not in seen_ids
        available_questions = Question.objects.exclude(id__in=seen_ids)
        
        if not available_questions.exists():
            return Response(
                {"error": "No cached questions available", "should_generate": True},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get a random question
        count = available_questions.count()
        random_index = random.randint(0, count - 1)
        question = available_questions[random_index]
        
        serializer = self.get_serializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='smart-next')
    def smart_next(self, request):
        """
        Smart endpoint: tries to get a cached question first, falls back to generation.
        POST /api/questiongen/questions/smart-next/
        Body: {
            "seen_ids": [1, 2, 3],  # IDs user has already seen
            "prefer_cached": true   # If true, prefer cached over new generation
        }
        """
        seen_ids = request.data.get('seen_ids', [])
        prefer_cached = request.data.get('prefer_cached', True)
        
        # First try to get a cached question
        available_questions = Question.objects.exclude(id__in=seen_ids)
        
        if prefer_cached and available_questions.exists():
            # Return a random cached question
            count = available_questions.count()
            random_index = random.randint(0, count - 1)
            question = available_questions[random_index]
            
            serializer = self.get_serializer(question)
            response_data = serializer.data
            response_data['source'] = 'cached'
            return Response(response_data, status=status.HTTP_200_OK)
        
        # No cached questions available or prefer_cached is False, generate new
        seeds = parse_simulation_questions()
        if not seeds:
            return Response(
                {"error": "No seed questions available"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        seed = random.choice(seeds)
        result = generate_question(seed)
        
        if "error" in result:
            # If generation fails but we have cached questions, return one anyway
            if available_questions.exists():
                count = available_questions.count()
                random_index = random.randint(0, count - 1)
                question = available_questions[random_index]
                serializer = self.get_serializer(question)
                response_data = serializer.data
                response_data['source'] = 'cached_fallback'
                return Response(response_data, status=status.HTTP_200_OK)
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Save new question to database
        question = Question.objects.create(
            topic=result.get('topic', 'general'),
            question_text=result.get('question', ''),
            options=result.get('options', []),
            answer=result.get('answer', ''),
            explanation=result.get('explanation', ''),
            seed_question=seed
        )
        
        serializer = self.get_serializer(question)
        response_data = serializer.data
        response_data['source'] = 'generated'
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get statistics about cached questions.
        GET /api/questiongen/questions/stats/
        """
        total = Question.objects.count()
        by_topic = {}
        for q in Question.objects.values('topic').distinct():
            topic = q['topic']
            by_topic[topic] = Question.objects.filter(topic=topic).count()
        
        return Response({
            "total_cached": total,
            "by_topic": by_topic
        })

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


