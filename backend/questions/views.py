from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Question
from .serializers import QuestionSerializer
from .services.generator import generate_question, generate_question_for_topic, batch_generate as batch_generate_service
from .services.parser import parse_simulation_questions, parse_courseware, get_all_topics
from .services.courses import get_all_courses, get_course, get_default_course
import random
import re


def normalize_text(text):
    """Normalize text for comparison: lowercase, remove extra spaces, punctuation."""
    if not text:
        return ""
    # Remove code blocks and special formatting
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    # Remove punctuation and extra spaces
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_duplicate_question(question_text, course_id, threshold=0.85):
    """
    Check if a similar question already exists in the database.
    Uses simple word overlap ratio for similarity.
    Returns the existing question if duplicate, None otherwise.
    """
    normalized_new = normalize_text(question_text)
    new_words = set(normalized_new.split())
    
    if not new_words:
        return None
    
    # Only check questions from the same course
    existing_questions = Question.objects.filter(course_id=course_id)
    
    for q in existing_questions:
        normalized_existing = normalize_text(q.question_text)
        existing_words = set(normalized_existing.split())
        
        if not existing_words:
            continue
        
        # Calculate Jaccard similarity
        intersection = len(new_words & existing_words)
        union = len(new_words | existing_words)
        
        if union > 0:
            similarity = intersection / union
            if similarity >= threshold:
                return q  # Found duplicate
    
    return None


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Custom authentication class that doesn't enforce CSRF for API calls."""
    def enforce_csrf(self, request):
        return  # Skip CSRF check



class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for questions.
    Supports multi-course system.
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]  # 豁免 CSRF 检查

    def get_queryset(self):
        """Filter queryset by course_id if provided."""
        queryset = Question.objects.all()
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='courses')
    def courses(self, request):
        """
        Get all available courses.
        GET /api/questions/courses/
        """
        courses = get_all_courses()
        default = get_default_course()
        return Response({
            "courses": courses,
            "default": default
        })

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """
        Generate a single question from a provided seed or random seed.
        POST /api/questions/generate/
        Body: {
            "seed": "optional seed question text",
            "course_id": "course identifier (optional, uses default)"
        }
        """
        seed = request.data.get('seed')
        course_id = request.data.get('course_id') or get_default_course()
        
        if not seed:
            # Use a random seed from simulation questions
            seeds = parse_simulation_questions(course_id)
            if not seeds:
                return Response(
                    {"error": "No seed questions available for this course"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            seed = random.choice(seeds)
        
        result = generate_question(seed, course_id)
        
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Save to database
        question = Question.objects.create(
            course_id=course_id,
            topic=result.get('topic', 'general'),
            difficulty=result.get('difficulty', 'medium'),
            question_text=result.get('question', ''),
            options=result.get('options', []),
            answer=result.get('answer', ''),
            explanation=result.get('explanation', ''),
            seed_question=seed
        )
        
        serializer = self.get_serializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='smart-next')
    def smart_next(self, request):
        """
        Get the next question intelligently.
        Prioritizes cached questions over generation, filters by topic, and excludes seen questions.
        POST /api/questions/smart-next/
        Body: {
            "seen_ids": [1, 2, 3],
            "generate_if_empty": true,
            "topic": "topic-name",
            "difficulty": "easy" or "medium" or "hard" or null,
            "course_id": "course identifier"
        }
        """
        seen_ids = request.data.get('seen_ids', [])
        generate_if_empty = request.data.get('generate_if_empty', True)
        topic = request.data.get('topic')
        difficulty = request.data.get('difficulty')
        course_id = request.data.get('course_id') or get_default_course()
        
        # Build query for cached questions
        queryset = Question.objects.filter(course_id=course_id)
        
        # Exclude seen questions
        if seen_ids:
            queryset = queryset.exclude(id__in=seen_ids)
        
        # Filter by topic if provided (exact match, case-insensitive)
        if topic:
            queryset = queryset.filter(topic__iexact=topic)
        
        # Filter by difficulty if provided
        if difficulty and difficulty in ['easy', 'medium', 'hard']:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Try to get a random cached question
        cached_questions = list(queryset)
        
        if cached_questions:
            # Return a random cached question
            question = random.choice(cached_questions)
            serializer = self.get_serializer(question)
            data = serializer.data
            data['source'] = 'cached'
            return Response(data)
        
        # No cached questions available
        if not generate_if_empty:
            return Response(
                {"error": "No questions available", "source": "none"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate a new question
        try:
            if topic:
                # Generate question for specific topic with target difficulty
                result = generate_question_for_topic(topic, course_id, target_difficulty=difficulty)
            else:
                # Generate question from random seed
                seeds = parse_simulation_questions(course_id)
                if not seeds:
                    return Response(
                        {"error": "No seed questions available for this course"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                seed = random.choice(seeds)
                result = generate_question(seed, course_id, target_difficulty=difficulty)
            
            if "error" in result:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Check for duplicate before saving
            new_question_text = result.get('question', '')
            existing = is_duplicate_question(new_question_text, course_id)
            if existing:
                # Return existing question instead of creating duplicate
                serializer = self.get_serializer(existing)
                data = serializer.data
                data['source'] = 'cached'
                data['deduplicated'] = True
                return Response(data)
            
            # Save to database
            # Use the user-selected topic if provided, otherwise use AI's inferred topic
            saved_topic = topic if topic else result.get('topic', 'general')
            question = Question.objects.create(
                course_id=course_id,
                topic=saved_topic,
                difficulty=result.get('difficulty', 'medium'),
                question_text=new_question_text,
                options=result.get('options', []),
                answer=result.get('answer', ''),
                explanation=result.get('explanation', ''),
                seed_question=result.get('seed_question', '')
            )
            
            serializer = self.get_serializer(question)
            data = serializer.data
            data['source'] = 'generated'
            return Response(data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='batch-generate')
    def batch_generate(self, request):
        """
        Generate multiple questions from all seeds.
        POST /api/questions/batch-generate/
        Body: {
            "limit": 5,
            "course_id": "course identifier"
        }
        """
        limit = request.data.get('limit', 5)
        course_id = request.data.get('course_id') or get_default_course()
        
        results = batch_generate_service(course_id, limit=limit)
        
        created_questions = []
        for result in results:
            if "error" not in result:
                question = Question.objects.create(
                    course_id=course_id,
                    topic=result.get('topic', 'general'),
                    difficulty=result.get('difficulty', 'medium'),
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
        Get available topics for a course.
        GET /api/questions/topics/?course_id=xxx
        """
        course_id = request.query_params.get('course_id') or get_default_course()
        
        # Get topics from courseware
        context = parse_courseware(course_id)
        courseware_topics = list(context.keys())
        
        # Get topics from database (unique values for this course)
        db_topics = list(
            Question.objects.filter(course_id=course_id)
            .values_list('topic', flat=True)
            .distinct()
        )
        
        return Response({
            "course_id": course_id,
            "topics": db_topics,
            "courseware_topics": courseware_topics
        })

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get statistics about cached questions.
        GET /api/questions/stats/?course_id=xxx
        """
        course_id = request.query_params.get('course_id')
        
        if course_id:
            queryset = Question.objects.filter(course_id=course_id)
        else:
            queryset = Question.objects.all()
        
        total = queryset.count()
        
        # Count questions by topic
        by_topic = {}
        topic_counts = queryset.values('topic').annotate(count=Count('id'))
        for item in topic_counts:
            by_topic[item['topic']] = item['count']
        
        # Count by course
        by_course = {}
        course_counts = Question.objects.values('course_id').annotate(count=Count('id'))
        for item in course_counts:
            by_course[item['course_id']] = item['count']
        
        return Response({
            "total_cached": total,
            "by_topic": by_topic,
            "by_course": by_course,
            "current_course": course_id
        })

    @action(detail=False, methods=['post'], url_path='chat')
    def chat(self, request):
        """
        AI Chat endpoint with two modes (non-streaming).
        POST /api/questions/chat/
        """
        from .services.chat import chat_qa_mode, chat_review_mode
        
        mode = request.data.get('mode', 'qa')
        messages = request.data.get('messages', [])
        current_question = request.data.get('current_question', {})
        course_id = request.data.get('course_id')
        
        if not messages:
            return Response({"error": "No messages provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not current_question:
            return Response({"error": "No current question provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        if mode == 'qa':
            result = chat_qa_mode(messages, current_question, course_id)
        elif mode == 'review':
            result = chat_review_mode(messages, current_question, course_id)
        else:
            return Response({"error": f"Unknown mode: {mode}"}, status=status.HTTP_400_BAD_REQUEST)
        
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(result)

    @action(detail=False, methods=['post'], url_path='chat-stream')
    def chat_stream(self, request):
        """
        Streaming AI Chat endpoint with SSE.
        POST /api/questions/chat-stream/
        Returns Server-Sent Events stream.
        """
        from django.http import StreamingHttpResponse
        from .services.chat import chat_stream as stream_chat
        import json
        
        mode = request.data.get('mode', 'qa')
        messages = request.data.get('messages', [])
        current_question = request.data.get('current_question', {})
        course_id = request.data.get('course_id')
        
        if not messages or not current_question:
            def error_stream():
                yield f"data: {json.dumps({'error': 'Missing required data'})}\n\n"
            return StreamingHttpResponse(error_stream(), content_type='text/event-stream')
        
        def event_stream():
            for item in stream_chat(mode, messages, current_question, course_id):
                yield f"data: {json.dumps(item)}\n\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    @action(detail=True, methods=['post'], url_path='request-delete')
    def request_delete(self, request, pk=None):
        """
        Request to delete a question with reasoner confirmation.
        POST /api/questions/{id}/request-delete/
        Body: {
            "conversation_history": [messages],
            "reason": "brief reason"
        }
        """
        from .services.chat import confirm_deletion_with_reasoner
        
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        conversation_history = request.data.get('conversation_history', [])
        
        # Prepare question data for reasoner
        question_data = {
            "id": question.id,
            "topic": question.topic,
            "question_text": question.question_text,
            "options": question.options,
            "answer": question.answer,
            "explanation": question.explanation
        }
        
        # Get reasoner confirmation
        result = confirm_deletion_with_reasoner(conversation_history, question_data)
        
        if result.get("confirmed"):
            # Delete the question
            question_id = question.id
            question.delete()
            return Response({
                "deleted": True,
                "question_id": question_id,
                "reasoning": result.get("reasoning", "")
            })
        else:
            return Response({
                "deleted": False,
                "reasoning": result.get("reasoning", "Deletion not confirmed by reasoner.")
            })
