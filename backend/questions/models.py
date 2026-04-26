from django.db import models


class KnowledgePoint(models.Model):
    """A structured study unit extracted from courseware.

    Each chapter (topic) splits into N points where N is decided by
    coverage rather than a fixed quota. A point is meant to be small enough
    to memorise on its own — one concept, one sentence definition, a handful
    of supporting bullets, and the source excerpt it was distilled from.
    """

    IMPORTANCE_CHOICES = [
        ("core", "Core"),
        ("supporting", "Supporting"),
    ]

    course_id = models.CharField(max_length=100, db_index=True)
    topic = models.CharField(max_length=100, db_index=True)
    sequence = models.PositiveIntegerField(default=0, db_index=True)
    title = models.CharField(max_length=200)
    definition = models.TextField()           # one-sentence definition
    details = models.JSONField(default=list)  # list of markdown bullet strings
    importance = models.CharField(
        max_length=16,
        choices=IMPORTANCE_CHOICES,
        default="core",
    )
    source_excerpt = models.TextField(blank=True, default="")  # short quoted text from courseware
    source_chapter = models.CharField(max_length=200, blank=True, default="")  # human-readable chapter label
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course_id", "topic", "sequence", "id"]
        indexes = [
            models.Index(fields=["course_id", "topic"]),
            models.Index(fields=["course_id", "topic", "sequence"]),
        ]

    def __str__(self):
        return f"[{self.course_id}/{self.topic}] {self.title}"


class Question(models.Model):
    """Generated question with answer and explanation.

    Supports three types via `question_type`:
    - mcq    选择题:   options=[A,B,C,D], answer="A. ...", explanation
    - fill   填空题:   options=null,  answer="正确填空内容（可含'|||'分隔多个空）",  explanation
    - essay  论述题:   options=null,  answer="参考答案",  explanation 含评分要点 rubric
    """

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    QUESTION_TYPE_CHOICES = [
        ("mcq", "Multiple Choice"),
        ("fill", "Fill in the Blank"),
        ("essay", "Essay / Discussion"),
    ]

    course_id = models.CharField(max_length=100, db_index=True, default="software-tools")
    topic = models.CharField(max_length=100, db_index=True)
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPE_CHOICES,
        default="mcq",
        db_index=True,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default="medium",
        db_index=True,
    )
    question_text = models.TextField()
    options = models.JSONField(blank=True, null=True)  # List of 4 options for mcq, null for fill/essay
    answer = models.TextField()  # widened from CharField(500) — essay answers can be long
    explanation = models.TextField()
    seed_question = models.TextField(blank=True, null=True)
    source_files = models.JSONField(blank=True, null=True, default=list)  # List of source file paths
    # Citation — populated by the generator so the explanation can cite the
    # exact chapter / passage the answer came from. Backfilled for existing
    # rows by `manage.py backfill_citations`.
    source_chapter = models.CharField(max_length=200, blank=True, default="")
    source_excerpt = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["course_id", "topic"]),
            models.Index(fields=["course_id", "difficulty"]),
            models.Index(fields=["course_id", "question_type"]),
        ]

    def __str__(self):
        return f"[{self.course_id}] [{self.question_type}/{self.difficulty}] {self.topic}: {self.question_text[:50]}..."
