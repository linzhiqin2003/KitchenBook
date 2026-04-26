from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Question, KnowledgePoint
from .serializers import QuestionSerializer, KnowledgePointSerializer
from .services.generator import (
    generate_question,
    generate_question_for_topic,
    generate_fill_question,
    generate_essay_question,
    generate_knowledge_points,
    grade_essay_answer,
    grade_fill_answer,
    batch_generate as batch_generate_service,
    batch_generate_typed,
)
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
            seed_question=seed,
            source_chapter=result.get('source_chapter', ''),
            source_excerpt=result.get('source_excerpt', ''),
        )
        
        serializer = self.get_serializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='smart-next')
    def smart_next(self, request):
        """
        Get the next question intelligently.
        Prioritizes cached questions over generation, filters by topic/type/difficulty, excludes seen.
        POST /api/questions/smart-next/
        Body: {
            "seen_ids": [1, 2, 3],
            "generate_if_empty": true,
            "topic": "topic-name",
            "difficulty": "easy" or "medium" or "hard" or null,
            "question_type": "mcq" | "fill" | "essay" | null  (defaults to "mcq" for back-compat),
            "course_id": "course identifier"
        }
        """
        seen_ids = request.data.get('seen_ids', [])
        generate_if_empty = request.data.get('generate_if_empty', True)
        topic = request.data.get('topic')
        difficulty = request.data.get('difficulty')
        question_type = request.data.get('question_type') or 'mcq'
        course_id = request.data.get('course_id') or get_default_course()

        if question_type not in ('mcq', 'fill', 'essay'):
            return Response({"error": f"Invalid question_type: {question_type}"}, status=status.HTTP_400_BAD_REQUEST)

        # Build query for cached questions
        queryset = Question.objects.filter(course_id=course_id, question_type=question_type)

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

        # Generate a new question, dispatched by type
        try:
            if question_type == 'mcq':
                if topic:
                    result = generate_question_for_topic(topic, course_id, target_difficulty=difficulty)
                else:
                    seeds = parse_simulation_questions(course_id)
                    if not seeds:
                        # Fall back to topic-based generation when no seed simulation file exists
                        ctx = parse_courseware(course_id)
                        if not ctx:
                            return Response({"error": "No courseware available for this course"}, status=status.HTTP_400_BAD_REQUEST)
                        random_topic = random.choice(list(ctx.keys()))
                        result = generate_question_for_topic(random_topic, course_id, target_difficulty=difficulty)
                    else:
                        seed = random.choice(seeds)
                        result = generate_question(seed, course_id, target_difficulty=difficulty)
            elif question_type == 'fill':
                effective_topic = topic
                if not effective_topic:
                    ctx = parse_courseware(course_id)
                    if not ctx:
                        return Response({"error": "No courseware available"}, status=status.HTTP_400_BAD_REQUEST)
                    effective_topic = random.choice(list(ctx.keys()))
                result = generate_fill_question(effective_topic, course_id, target_difficulty=difficulty)
            else:  # essay
                effective_topic = topic
                if not effective_topic:
                    ctx = parse_courseware(course_id)
                    if not ctx:
                        return Response({"error": "No courseware available"}, status=status.HTTP_400_BAD_REQUEST)
                    effective_topic = random.choice(list(ctx.keys()))
                result = generate_essay_question(effective_topic, course_id, target_difficulty=difficulty)

            if "error" in result:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Dedupe (only meaningful for mcq/fill — essay prompts are hand-crafted enough)
            new_question_text = result.get('question', '')
            if question_type in ('mcq', 'fill'):
                existing = is_duplicate_question(new_question_text, course_id)
                if existing and existing.question_type == question_type:
                    serializer = self.get_serializer(existing)
                    data = serializer.data
                    data['source'] = 'cached'
                    data['deduplicated'] = True
                    return Response(data)

            saved_topic = topic if topic else result.get('topic', 'general')
            question = Question.objects.create(
                course_id=course_id,
                topic=saved_topic,
                question_type=question_type,
                difficulty=result.get('difficulty', 'medium'),
                question_text=new_question_text,
                options=result.get('options') if question_type == 'mcq' else None,
                answer=result.get('answer', ''),
                explanation=result.get('explanation', ''),
                seed_question=result.get('seed_question', ''),
                source_chapter=result.get('source_chapter', ''),
                source_excerpt=result.get('source_excerpt', ''),
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
        Generate multiple questions of a chosen type, distributed across topics.
        POST /api/questions/batch-generate/
        Body: {
            "limit": 5,
            "course_id": "course identifier",
            "question_type": "mcq" | "fill" | "essay" (default "mcq"),
            "topic": "topic-name"  (optional — restrict to a single topic),
            "difficulty": "easy" | "medium" | "hard" (optional)
        }

        Back-compat: if question_type is omitted AND no courseware topics are usable
        AND simulation seeds exist, falls back to legacy seed-based MCQ generation.
        """
        limit = int(request.data.get('limit', 5))
        course_id = request.data.get('course_id') or get_default_course()
        question_type = request.data.get('question_type') or 'mcq'
        topic = request.data.get('topic')
        difficulty = request.data.get('difficulty')

        if question_type not in ('mcq', 'fill', 'essay'):
            return Response({"error": f"Invalid question_type: {question_type}"}, status=status.HTTP_400_BAD_REQUEST)

        # Prefer topic-distributed batch generator (works for all types)
        ctx = parse_courseware(course_id)
        if ctx:
            results = batch_generate_typed(course_id, question_type, limit, target_difficulty=difficulty, topic=topic)
        elif question_type == 'mcq':
            # Legacy fallback: only mcq supports the old seed-based generator
            results = batch_generate_service(course_id, limit=limit)
        else:
            return Response({"error": "No courseware available for this course"}, status=status.HTTP_400_BAD_REQUEST)

        created_questions = []
        for result in results:
            if "error" in result:
                continue
            qtype = result.get('question_type', question_type)
            qtext = result.get('question', '')
            # Dedupe within mcq/fill before insert
            if qtype in ('mcq', 'fill'):
                existing = is_duplicate_question(qtext, course_id)
                if existing and existing.question_type == qtype:
                    continue
            question = Question.objects.create(
                course_id=course_id,
                topic=topic if topic else result.get('topic', 'general'),
                question_type=qtype,
                difficulty=result.get('difficulty', 'medium'),
                question_text=qtext,
                options=result.get('options') if qtype == 'mcq' else None,
                answer=result.get('answer', ''),
                explanation=result.get('explanation', ''),
                seed_question=result.get('seed_question', ''),
                source_chapter=result.get('source_chapter', ''),
                source_excerpt=result.get('source_excerpt', ''),
            )
            created_questions.append(question)

        serializer = self.get_serializer(created_questions, many=True)
        return Response({
            "generated": len(created_questions),
            "questions": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='grade')
    def grade(self, request, pk=None):
        """
        Grade a student's answer for fill or essay questions.
        POST /api/questions/{id}/grade/
        Body: {
            "answer": "the student's answer text"  (for fill: separate multi-blanks with '|||')
        }
        Returns:
            For fill: {correct: bool, per_blank: [bool], expected: [str]}
            For essay: {score: 0-10, max_score: 10, matched_points: [...], missing_points: [...], feedback: str}
        """
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)

        student_answer = request.data.get('answer', '')

        if question.question_type == 'fill':
            return Response(grade_fill_answer(question.answer, student_answer))

        if question.question_type == 'essay':
            result = grade_essay_answer(
                question.question_text,
                question.answer,
                question.explanation,  # rubric stored in explanation
                student_answer,
                course_id=question.course_id,
                generation_context=question.generation_context,
            )
            if "error" in result:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(result)

        # mcq questions are graded client-side; reject explicit grade calls
        return Response({"error": "MCQ questions are graded client-side"}, status=status.HTTP_400_BAD_REQUEST)

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
        for item in queryset.values('topic').annotate(count=Count('id')):
            by_topic[item['topic']] = item['count']

        # Count by question_type within current course
        by_type = {}
        for item in queryset.values('question_type').annotate(count=Count('id')):
            by_type[item['question_type']] = item['count']

        # Count by topic + type (for richer UI breakdown)
        by_topic_type = {}
        for item in queryset.values('topic', 'question_type').annotate(count=Count('id')):
            by_topic_type.setdefault(item['topic'], {})[item['question_type']] = item['count']

        # Count by course
        by_course = {}
        for item in Question.objects.values('course_id').annotate(count=Count('id')):
            by_course[item['course_id']] = item['count']

        return Response({
            "total_cached": total,
            "by_topic": by_topic,
            "by_type": by_type,
            "by_topic_type": by_topic_type,
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


class CoursewareView(viewsets.ViewSet):
    """Read-only access to the raw courseware (the source markdown the AI was
    fed). Lets the user browse the original chapter content directly.
    """
    authentication_classes = [CsrfExemptSessionAuthentication]

    @action(detail=False, methods=['get'], url_path='chapter')
    def chapter(self, request):
        """GET /api/questiongen/courseware/chapter/?course_id=X&topic=Y

        Returns the markdown body for one chapter so the frontend can render
        it as a read-only document.
        """
        course_id = request.query_params.get('course_id') or get_default_course()
        topic = request.query_params.get('topic')
        if not topic:
            return Response({"error": "topic required"}, status=status.HTTP_400_BAD_REQUEST)

        ctx = parse_courseware(course_id)
        match = None
        for k in ctx.keys():
            if k.lower() == topic.lower():
                match = k
                break
        if not match:
            return Response({"error": "topic not found in courseware"},
                            status=status.HTTP_404_NOT_FOUND)
        body = ctx[match]
        return Response({
            "course_id": course_id,
            "topic": match,
            "content": body,
            "char_count": len(body),
            "line_count": body.count("\n") + 1,
        })

    @action(detail=False, methods=['get'], url_path='topics')
    def topics(self, request):
        """List chapter ids + their character counts for a course."""
        course_id = request.query_params.get('course_id') or get_default_course()
        ctx = parse_courseware(course_id)
        return Response({
            "course_id": course_id,
            "topics": [
                {"topic": t, "char_count": len(content)}
                for t, content in ctx.items()
            ],
        })


class KnowledgePointViewSet(viewsets.ReadOnlyModelViewSet):
    """List + lazily-generate study notes (knowledge points) for a course/topic."""
    queryset = KnowledgePoint.objects.all()
    serializer_class = KnowledgePointSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get_queryset(self):
        qs = KnowledgePoint.objects.all()
        course_id = self.request.query_params.get('course_id')
        topic = self.request.query_params.get('topic')
        if course_id:
            qs = qs.filter(course_id=course_id)
        if topic:
            qs = qs.filter(topic__iexact=topic)
        return qs.order_by('topic', 'sequence', 'id')

    @action(detail=False, methods=['get'], url_path='topics')
    def topics(self, request):
        """Per-course list of topics with their note counts.

        Returns: {course_id, topics: [{topic, count}], courseware_topics: [...]}
        """
        course_id = request.query_params.get('course_id') or get_default_course()
        ctx = parse_courseware(course_id)
        courseware_topics = list(ctx.keys())

        counts = {}
        for row in KnowledgePoint.objects.filter(course_id=course_id).values('topic').annotate(n=Count('id')):
            counts[row['topic']] = row['n']

        topics = [{"topic": t, "count": counts.get(t, 0)} for t in courseware_topics]
        return Response({
            "course_id": course_id,
            "topics": topics,
        })

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """Generate (or regenerate) all knowledge points for one course+topic.

        Body: { "course_id": str, "topic": str, "replace": bool=true }
        """
        course_id = request.data.get('course_id') or get_default_course()
        topic = request.data.get('topic')
        replace = request.data.get('replace', True)

        if not topic:
            return Response({"error": "topic required"}, status=status.HTTP_400_BAD_REQUEST)

        result = generate_knowledge_points(topic, course_id)
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        points = result.get("points", []) or []
        canonical_topic = result.get("topic", topic)

        if replace:
            KnowledgePoint.objects.filter(course_id=course_id, topic=canonical_topic).delete()

        created = []
        for i, p in enumerate(points):
            kp = KnowledgePoint.objects.create(
                course_id=course_id,
                topic=canonical_topic,
                sequence=i,
                title=(p.get('title') or '').strip()[:200],
                definition=(p.get('definition') or '').strip(),
                details=p.get('details') or [],
                importance=p.get('importance') if p.get('importance') in ('core', 'supporting') else 'core',
                source_excerpt=(p.get('source_excerpt') or '').strip(),
                source_chapter=(p.get('source_chapter') or '').strip()[:200],
            )
            created.append(kp)

        serializer = self.get_serializer(created, many=True)
        return Response({
            "topic": canonical_topic,
            "course_id": course_id,
            "generated": len(created),
            "points": serializer.data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='batch-generate')
    def batch_generate(self, request):
        """Generate notes for every topic in a course (skips topics that already have any).

        Body: { "course_id": str, "force": bool=false }
        """
        course_id = request.data.get('course_id') or get_default_course()
        force = bool(request.data.get('force'))

        ctx = parse_courseware(course_id)
        if not ctx:
            return Response({"error": "No courseware found"}, status=status.HTTP_400_BAD_REQUEST)

        summary = []
        for topic in ctx.keys():
            existing = KnowledgePoint.objects.filter(course_id=course_id, topic=topic).count()
            if existing and not force:
                summary.append({"topic": topic, "skipped": True, "existing": existing})
                continue
            result = generate_knowledge_points(topic, course_id, ctx)
            if "error" in result:
                summary.append({"topic": topic, "error": result["error"]})
                continue
            points = result.get("points", []) or []
            if force:
                KnowledgePoint.objects.filter(course_id=course_id, topic=topic).delete()
            for i, p in enumerate(points):
                KnowledgePoint.objects.create(
                    course_id=course_id,
                    topic=topic,
                    sequence=i,
                    title=(p.get('title') or '').strip()[:200],
                    definition=(p.get('definition') or '').strip(),
                    details=p.get('details') or [],
                    importance=p.get('importance') if p.get('importance') in ('core', 'supporting') else 'core',
                    source_excerpt=(p.get('source_excerpt') or '').strip(),
                    source_chapter=(p.get('source_chapter') or '').strip()[:200],
                )
            summary.append({"topic": topic, "generated": len(points)})
        return Response({"course_id": course_id, "summary": summary})
