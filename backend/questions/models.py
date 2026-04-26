from django.db import models


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
