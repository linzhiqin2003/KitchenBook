"""Pre-generate multiple-choice questions for one or more topics.

For each topic the LLM gets:
  - The topic's courseware (subject matter, sampled to fit 50k char window).
  - A randomly picked seed question from the course's mock paper(s) (style hint).

Each call produces one mcq; the result is deduped against existing rows
(Jaccard similarity) before being saved.

Examples:

    # Pre-bake 20 questions for every chapter 11-20:
    python manage.py pregenerate_mcq \\
        --course software-tools \\
        --topics http,html,css,css-layout,js-basics,js-advanced,scraping,pgp,protocols,testing \\
        --per-topic 20 \\
        --concurrency 4 \\
        --apply

    # Single chapter, dry-run (prints questions, doesn't write):
    python manage.py pregenerate_mcq --course software-tools --topics http --per-topic 5
"""
from __future__ import annotations

import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand, CommandError

from questions.models import Question
from questions.services.generator import generate_question_for_topic
from questions.services.parser import parse_courseware, parse_simulation_questions


def _normalize(text):
    """Match the dedupe normalisation used by views.is_duplicate_question."""
    import re
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _is_duplicate(text, course_id, threshold=0.85):
    """Same Jaccard check views.is_duplicate_question performs.

    Reimplemented locally so this command stays a pure ORM/services consumer
    (no `views` import).
    """
    new_words = set(_normalize(text).split())
    if not new_words:
        return None
    for q in Question.objects.filter(course_id=course_id).only("id", "question_text"):
        existing_words = set(_normalize(q.question_text).split())
        if not existing_words:
            continue
        union = len(new_words | existing_words)
        if union and (len(new_words & existing_words) / union) >= threshold:
            return q
    return None


def _generate_one(topic, course_id, context_data, seeds, target_difficulty=None):
    """Generate a single mcq for `topic`, with a random seed sampled per call."""
    seed = random.choice(seeds) if seeds else None
    return generate_question_for_topic(
        topic,
        course_id=course_id,
        context_data=context_data,
        target_difficulty=target_difficulty,
        seed_question=seed,
    )


class Command(BaseCommand):
    help = "Pre-bake mcq questions for the given topics using the mock paper as a style reference."

    def add_arguments(self, parser):
        parser.add_argument("--course", type=str, default="software-tools",
                            help="Course id (default: software-tools).")
        parser.add_argument("--topics", type=str, required=True,
                            help="Comma-separated topic names (parsed form, e.g. 'http,html,css').")
        parser.add_argument("--per-topic", type=int, default=20,
                            help="How many questions to generate per topic (default: 20).")
        parser.add_argument("--difficulty-mix", type=str, default="3:13:4",
                            help="easy:medium:hard ratio per topic (default 3:13:4 ≈ 15/65/20%%).")
        parser.add_argument("--concurrency", type=int, default=4,
                            help="Parallel LLM calls per topic.")
        parser.add_argument("--max-attempts-multiplier", type=int, default=3,
                            help="Allow up to N×per-topic attempts to absorb LLM/dedupe failures.")
        parser.add_argument("--apply", action="store_true",
                            help="Persist results to DB. Without this flag the command is dry-run.")

    def handle(self, *args, **opts):
        course_id = opts["course"]
        topics = [t.strip() for t in opts["topics"].split(",") if t.strip()]
        per_topic = opts["per_topic"]
        concurrency = opts["concurrency"]
        max_attempts = per_topic * opts["max_attempts_multiplier"]
        apply_changes = opts["apply"]
        diff_mix = self._parse_difficulty_mix(opts["difficulty_mix"], per_topic)

        context_data = parse_courseware(course_id)
        if not context_data:
            raise CommandError(f"No courseware found for course '{course_id}'.")
        seeds = parse_simulation_questions(course_id) or []
        if not seeds:
            self.stdout.write(self.style.WARNING(
                f"No simulation seeds found for '{course_id}'. Falling back to topic-only prompts."
            ))

        # Validate topics resolve against the parsed courseware.
        available = {k.lower(): k for k in context_data.keys()}
        unresolved = [t for t in topics if t.lower() not in available]
        if unresolved:
            self.stdout.write(self.style.WARNING(
                f"Topics not directly matched (will fall back to fuzzy): {unresolved}\n"
                f"Available topics: {sorted(available.values())}"
            ))

        if not apply_changes:
            self.stdout.write(self.style.NOTICE("DRY RUN — pass --apply to persist."))

        total_saved = 0
        total_failed = 0
        t0 = time.time()
        for topic in topics:
            saved, failed = self._run_topic(
                topic, course_id, context_data, seeds,
                per_topic, diff_mix, concurrency, max_attempts, apply_changes,
            )
            total_saved += saved
            total_failed += failed

        elapsed = time.time() - t0
        self.stdout.write(self.style.SUCCESS(
            f"\nFinished in {elapsed:.1f}s — saved={total_saved} failed/dup={total_failed} "
            f"across {len(topics)} topic(s)."
        ))

    def _parse_difficulty_mix(self, spec, per_topic):
        """Turn '3:13:4' + per_topic=20 into a list of difficulty strings of len per_topic."""
        try:
            e, m, h = (int(x) for x in spec.split(":"))
        except ValueError:
            raise CommandError(f"--difficulty-mix must look like 'E:M:H' (got {spec!r}).")
        total = e + m + h
        if total <= 0:
            raise CommandError("--difficulty-mix totals must be > 0.")
        # Allocate proportionally, fix any rounding leftover into 'medium'.
        n_easy = round(per_topic * e / total)
        n_hard = round(per_topic * h / total)
        n_medium = per_topic - n_easy - n_hard
        plan = (["easy"] * n_easy) + (["medium"] * n_medium) + (["hard"] * n_hard)
        random.shuffle(plan)
        return plan

    def _run_topic(self, topic, course_id, context_data, seeds, per_topic, diff_mix,
                   concurrency, max_attempts, apply_changes):
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n=== Topic '{topic}' — target {per_topic} mcq (concurrency={concurrency}) ==="
        ))

        saved = 0
        failed = 0
        attempts = 0
        # We submit one job at a time (so we always know which difficulty slot we're filling)
        # but pipe up to `concurrency` jobs in flight via a small bounded pool.
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {}

            def submit_next():
                nonlocal attempts
                if saved + len(futures) >= per_topic:
                    return False
                if attempts >= max_attempts:
                    return False
                difficulty = diff_mix[saved + len(futures)] if (saved + len(futures)) < len(diff_mix) else None
                fut = pool.submit(
                    _generate_one,
                    topic, course_id, context_data, seeds, difficulty,
                )
                futures[fut] = difficulty
                attempts += 1
                return True

            # prime the pool
            for _ in range(concurrency):
                if not submit_next():
                    break

            while futures and saved < per_topic:
                done = next(as_completed(futures))
                difficulty = futures.pop(done)
                try:
                    result = done.result()
                except Exception as exc:
                    failed += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ generator crashed: {exc}"))
                    submit_next()
                    continue

                if not result or "error" in result:
                    failed += 1
                    err = (result or {}).get("error", "empty result")
                    self.stdout.write(self.style.WARNING(f"  ! generation error: {err}"))
                    submit_next()
                    continue

                qtext = result.get("question", "").strip()
                if not qtext:
                    failed += 1
                    submit_next()
                    continue

                dup = _is_duplicate(qtext, course_id)
                if dup is not None:
                    failed += 1
                    self.stdout.write(f"  ~ dup of #{dup.id}, skipping")
                    submit_next()
                    continue

                if apply_changes:
                    Question.objects.create(
                        course_id=course_id,
                        topic=topic,
                        question_type="mcq",
                        difficulty=result.get("difficulty", difficulty or "medium"),
                        question_text=qtext,
                        options=result.get("options", []),
                        answer=result.get("answer", ""),
                        explanation=result.get("explanation", ""),
                        seed_question=result.get("seed_question", ""),
                        source_chapter=result.get("source_chapter", ""),
                        source_excerpt=result.get("source_excerpt", ""),
                    )
                saved += 1
                preview = qtext[:80].replace("\n", " ")
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ [{saved}/{per_topic}] ({result.get('difficulty', '?')}) {preview}…"
                ))
                submit_next()

            # drain any still-running futures (shouldn't happen if loop ended on saved hit)
            for f in list(futures.keys()):
                f.cancel()

        if saved < per_topic:
            self.stdout.write(self.style.WARNING(
                f"  Only saved {saved}/{per_topic} for '{topic}' "
                f"(attempts={attempts}, failed={failed})."
            ))
        return saved, failed
