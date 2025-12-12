from django.db import models


class Question(models.Model):
    """Generated question with answer and explanation."""

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    course_id = models.CharField(max_length=100, db_index=True, default="software-tools")
    topic = models.CharField(max_length=100, db_index=True)
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default="medium",
        db_index=True,
    )
    question_text = models.TextField()
    options = models.JSONField()  # List of 4 options
    answer = models.CharField(max_length=500)
    explanation = models.TextField()
    seed_question = models.TextField(blank=True, null=True)
    source_files = models.JSONField(blank=True, null=True, default=list)  # List of source file paths
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["course_id", "topic"]),
            models.Index(fields=["course_id", "difficulty"]),
        ]

    def __str__(self):
        return f"[{self.course_id}] [{self.difficulty}] {self.topic}: {self.question_text[:50]}..."
