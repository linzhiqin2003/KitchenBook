from django.db import models

class Question(models.Model):
    """Generated question with answer and explanation."""
    topic = models.CharField(max_length=100, db_index=True)
    question_text = models.TextField()
    options = models.JSONField()  # List of 4 options
    answer = models.CharField(max_length=500)
    explanation = models.TextField()
    seed_question = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.topic}: {self.question_text[:50]}..."
