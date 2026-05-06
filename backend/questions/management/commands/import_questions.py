"""Import a JSON file of pre-baked Question rows into the database.

Idempotent: a row is skipped when an existing question with the same
`course_id` + `question_text` already exists. New rows get fresh primary
keys, so PK conflicts with rows already in the target DB are impossible.

Used to ferry questions from dev (SQLite) into prod (PostgreSQL) without
running the LLM generator twice.

Example:
    python manage.py import_questions \\
        --file courses/software-tools/fixtures/mcq_11_20.json
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from questions.models import Question


REQUIRED_FIELDS = {
    "course_id", "topic", "question_type", "difficulty",
    "question_text", "options", "answer", "explanation",
}


class Command(BaseCommand):
    help = "Import pre-baked Question rows from a JSON fixture (idempotent on course_id+question_text)."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True,
                            help="Path to the JSON fixture (list of dicts, no PKs).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show what would happen without writing.")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.is_file():
            raise CommandError(f"File not found: {path}")

        with path.open(encoding="utf-8") as f:
            rows = json.load(f)
        if not isinstance(rows, list):
            raise CommandError("Fixture must be a JSON list of objects.")

        created = 0
        skipped = 0
        bad = 0
        for i, row in enumerate(rows):
            missing = REQUIRED_FIELDS - row.keys()
            if missing:
                bad += 1
                self.stdout.write(self.style.WARNING(
                    f"  row {i}: missing fields {missing}, skipping"
                ))
                continue

            exists = Question.objects.filter(
                course_id=row["course_id"],
                question_text=row["question_text"],
            ).exists()
            if exists:
                skipped += 1
                continue

            if not opts["dry_run"]:
                Question.objects.create(
                    course_id=row["course_id"],
                    topic=row["topic"],
                    question_type=row["question_type"],
                    difficulty=row["difficulty"],
                    question_text=row["question_text"],
                    options=row.get("options"),
                    answer=row["answer"],
                    explanation=row["explanation"],
                    seed_question=row.get("seed_question") or "",
                    source_chapter=row.get("source_chapter") or "",
                    source_excerpt=row.get("source_excerpt") or "",
                )
            created += 1

        verb = "Would create" if opts["dry_run"] else "Created"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {created}, skipped {skipped} dup(s), {bad} malformed (total {len(rows)})."
        ))
