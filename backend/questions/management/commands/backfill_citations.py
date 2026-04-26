"""Retrofit `source_chapter` + `source_excerpt` onto questions generated
before the citation prompt landed.

For each question lacking a citation, asks DeepSeek to locate the exact
passage in the courseware that justifies the stated answer. Concurrent
to keep wall time low.

Usage:
    # Dry run: just count what would be updated.
    python manage.py backfill_citations --dry-run

    # Apply for one course:
    python manage.py backfill_citations --course c-programming

    # Apply for all courses, 8 concurrent:
    python manage.py backfill_citations --concurrency 8
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand
from questions.models import Question
from questions.services.generator import add_citation_to_question
from questions.services.parser import parse_courseware


class Command(BaseCommand):
    help = "Backfill source_chapter + source_excerpt on existing questions."

    def add_arguments(self, parser):
        parser.add_argument("--course", type=str, default=None,
                            help="Limit to one course id (default: all)")
        parser.add_argument("--type", type=str, default=None,
                            choices=["mcq", "fill", "essay"],
                            help="Limit to one question type")
        parser.add_argument("--dry-run", action="store_true",
                            help="Just report what would be updated")
        parser.add_argument("--limit", type=int, default=None,
                            help="Max questions to process")
        parser.add_argument("--concurrency", type=int, default=6,
                            help="Parallel LLM calls (default 6)")
        parser.add_argument("--all", action="store_true",
                            help="Re-cite even questions that already have a citation")

    def handle(self, *args, **opts):
        qs = Question.objects.all()
        if opts["course"]:
            qs = qs.filter(course_id=opts["course"])
        if opts["type"]:
            qs = qs.filter(question_type=opts["type"])
        if not opts["all"]:
            qs = qs.filter(source_chapter="").filter(source_excerpt="")
        if opts["limit"]:
            qs = qs[: opts["limit"]]

        questions = list(qs)
        total = len(questions)
        if not total:
            self.stdout.write(self.style.WARNING("Nothing to backfill."))
            return

        if opts["dry_run"]:
            self.stdout.write(self.style.NOTICE(f"Dry-run: would backfill {total} questions."))
            return

        # Pre-load courseware per course once
        ctx_cache = {}
        for q in questions:
            if q.course_id not in ctx_cache:
                ctx_cache[q.course_id] = parse_courseware(q.course_id)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Backfilling {total} questions with concurrency={opts['concurrency']}"
        ))

        ok = err = blank = 0
        t0 = time.time()
        done = 0

        def worker(q):
            try:
                result = add_citation_to_question(q, course_id=q.course_id, context_data=ctx_cache.get(q.course_id))
                return q, result, None
            except Exception as e:
                return q, None, e

        with ThreadPoolExecutor(max_workers=opts["concurrency"]) as pool:
            futures = [pool.submit(worker, q) for q in questions]
            for fut in as_completed(futures):
                q, result, exc = fut.result()
                done += 1
                if exc is not None:
                    err += 1
                    self.stdout.write(self.style.ERROR(
                        f"[{done:>3}/{total}] ERROR id={q.id}  {exc}"
                    ))
                    continue
                if not result or "error" in result:
                    err += 1
                    self.stdout.write(self.style.ERROR(
                        f"[{done:>3}/{total}] ERROR id={q.id}  {result.get('error') if result else 'no result'}"
                    ))
                    continue
                chapter = (result.get("source_chapter") or "").strip()[:200]
                excerpt = (result.get("source_excerpt") or "").strip()
                if not chapter and not excerpt:
                    blank += 1
                    self.stdout.write(self.style.WARNING(
                        f"[{done:>3}/{total}] BLANK id={q.id}  (model couldn't locate evidence)"
                    ))
                    continue
                Question.objects.filter(pk=q.pk).update(
                    source_chapter=chapter,
                    source_excerpt=excerpt,
                )
                ok += 1
                if done % 10 == 0:
                    self.stdout.write(f"[{done:>3}/{total}] OK id={q.id}  {chapter[:60]}")

        elapsed = time.time() - t0
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SUMMARY ==="))
        self.stdout.write(f"Updated:  {ok}")
        self.stdout.write(f"Blank:    {blank}  (model returned empty, kept as-is)")
        self.stdout.write(f"Errors:   {err}")
        self.stdout.write(f"Elapsed:  {elapsed:.1f}s ({elapsed/total:.1f}s/question avg)")
