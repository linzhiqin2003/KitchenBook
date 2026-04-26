"""Generate essay questions for every chapter using a mock exam paper as
the style + difficulty reference.

For each chapter the LLM is fed:
  - The WHOLE mock paper (stylistic context).
  - That chapter's courseware (subject matter).

It returns:
  - Originals lifted verbatim from the paper that match the chapter.
  - Fresh sample variants testing other aspects of the chapter.

Every produced question is saved with its full generation context so the
grader has the exact evidence the LLM saw at generation time.

Usage:
    python manage.py generate_essays_from_mock \
        --course software-engineering \
        --paper courses/software-engineering/simulation/mock_2025.md \
        --samples 2 \
        --concurrency 4 \
        --apply
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from django.core.management.base import BaseCommand

from questions.models import Question
from questions.services.generator import generate_essays_for_chapter_from_paper
from questions.services.parser import parse_courseware


def _rubric_to_explanation(rubric):
    """Turn a rubric_breakdown list into a markdown bullet list (the existing
    grading prompt expects markdown bullets in `explanation`)."""
    if not rubric:
        return ""
    lines = []
    for r in rubric:
        marks = r.get("marks", "")
        criterion = (r.get("criterion") or "").strip()
        kp = r.get("key_points") or []
        line = f"- ({marks} marks) **{criterion}**"
        lines.append(line)
        for p in kp:
            lines.append(f"    - {p}")
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Generate essay questions per chapter using a mock exam paper as reference."

    def add_arguments(self, parser):
        parser.add_argument("--course", type=str, default="software-engineering")
        parser.add_argument("--paper", type=str, required=True,
                            help="Path to the mock paper markdown (relative or absolute)")
        parser.add_argument("--samples", type=int, default=2,
                            help="Fresh sample variants per chapter (default 2)")
        parser.add_argument("--concurrency", type=int, default=3,
                            help="Parallel chapters (default 3 — each call is heavy)")
        parser.add_argument("--apply", action="store_true",
                            help="Actually save to DB. Default is dry-run.")
        parser.add_argument("--replace", action="store_true",
                            help="Delete existing essay questions for the course first.")

    def handle(self, *args, **opts):
        paper_path = Path(opts["paper"])
        # The command runs from `backend/` but `courses/` lives at the project
        # root. Search both locations so users can pass either a relative
        # path from the project root OR an absolute path.
        if not paper_path.is_absolute():
            backend_root = Path(__file__).resolve().parent.parent.parent.parent  # backend/
            project_root = backend_root.parent
            for candidate in (Path.cwd() / paper_path,
                              project_root / paper_path,
                              backend_root / paper_path):
                if candidate.exists():
                    paper_path = candidate
                    break
        if not paper_path.exists():
            self.stderr.write(self.style.ERROR(f"Paper not found: {paper_path}"))
            sys.exit(1)
        paper_text = paper_path.read_text(encoding="utf-8")

        course_id = opts["course"]
        ctx = parse_courseware(course_id)
        if not ctx:
            self.stderr.write(self.style.ERROR(f"No courseware for {course_id}"))
            sys.exit(1)

        chapters = list(ctx.keys())
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nGenerating essays for {len(chapters)} chapters of {course_id}\n"
            f"  paper: {paper_path}  ({len(paper_text)} chars)\n"
            f"  samples per chapter: {opts['samples']}\n"
            f"  concurrency: {opts['concurrency']}\n"
            f"  mode: {'APPLY' if opts['apply'] else 'DRY-RUN'}\n"
            f"  replace existing essays: {opts['replace']}\n"
        ))

        if opts["apply"] and opts["replace"]:
            n = Question.objects.filter(course_id=course_id, question_type="essay").count()
            Question.objects.filter(course_id=course_id, question_type="essay").delete()
            self.stdout.write(self.style.WARNING(f"Deleted {n} existing essay questions for {course_id}"))

        def work(chapter):
            t0 = time.time()
            r = generate_essays_for_chapter_from_paper(
                course_id, chapter, paper_text, context_data=ctx,
                num_samples=opts["samples"],
            )
            return chapter, r, time.time() - t0

        total_originals = total_samples = total_errors = 0
        all_results = []
        with ThreadPoolExecutor(max_workers=opts["concurrency"]) as pool:
            for chapter, result, dt in pool.map(work, chapters):
                if "error" in result:
                    total_errors += 1
                    self.stdout.write(self.style.ERROR(
                        f"  ✗ {chapter}: {result['error'][:120]} ({dt:.0f}s)"
                    ))
                    continue
                originals = result.get("originals", []) or []
                samples = result.get("samples", []) or []
                excerpt = result.get("_chapter_excerpt", "")
                total_originals += len(originals)
                total_samples += len(samples)
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ {chapter}: {len(originals)} originals + {len(samples)} samples ({dt:.0f}s)"
                ))
                all_results.append((chapter, originals, samples, excerpt))

        if not opts["apply"]:
            self.stdout.write(self.style.NOTICE(
                f"\nDry-run summary: would create {total_originals} originals + {total_samples} samples "
                f"({total_errors} chapters errored)"
            ))
            return

        # Persist
        created = 0
        for chapter, originals, samples, excerpt in all_results:
            for kind_originals, kind_label in ((originals, "original"), (samples, "sample")):
                for q in kind_originals:
                    if not q.get("question") or not q.get("answer"):
                        continue
                    explanation = _rubric_to_explanation(q.get("rubric_breakdown"))
                    Question.objects.create(
                        course_id=course_id,
                        topic=chapter,
                        question_type="essay",
                        difficulty="medium",
                        question_text=q.get("question", ""),
                        options=None,
                        answer=q.get("answer", ""),
                        explanation=explanation,
                        seed_question=("[mock 2025 original]" if kind_label == "original"
                                        else "[mock 2025 sample]"),
                        source_chapter=q.get("source_chapter", "")[:200],
                        source_excerpt=q.get("source_excerpt", ""),
                        generation_context={
                            "seed_paper_path": str(paper_path),
                            "seed_paper_excerpt": paper_text,
                            "chapter_id": chapter,
                            "chapter_excerpt": excerpt,
                            "marks_total": q.get("marks_total"),
                            "rubric_breakdown": q.get("rubric_breakdown") or [],
                            "is_original": kind_label == "original",
                        },
                    )
                    created += 1

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SUMMARY ==="))
        self.stdout.write(f"Originals extracted:  {total_originals}")
        self.stdout.write(f"Samples generated:    {total_samples}")
        self.stdout.write(f"Saved to DB:          {created}")
        self.stdout.write(f"Errors:               {total_errors}")
