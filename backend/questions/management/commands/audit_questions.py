"""Quality-audit existing questions with DeepSeek v4-flash + thinking mode.

For each MCQ question, the model judges:
  1. Is the question well-formed and answerable?
  2. Is the claimed answer correct?
  3. Is the claimed answer the ONLY correct option (no ambiguity)?
  4. Are the options distinct (no duplicates)?

If any of those fail with HIGH confidence, the question is deleted.

Before any deletion, a JSON backup is written so nothing is lost permanently.

Usage:
    # Dry-run on all courses (default — recommended first):
    python manage.py audit_questions --dry-run

    # Apply deletions for one course:
    python manage.py audit_questions --course c-programming --apply

    # Tune throughput:
    python manage.py audit_questions --course c-programming --apply --concurrency 5
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from common.deepseek_models import CHAT_MODEL, get_client as _get_deepseek_client, thinking_kwargs
from questions.models import Question
from questions.services.courses import get_course

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")
API_KEY = os.getenv("DEEPSEEK_API_KEY")


PROMPT_TEMPLATE = """你是严谨的考试题目审查员。请判断下面这道**单选题**是否应该保留在题库中。

## 课程
{course_name}

## 主题
{topic}

## 题干
{question_text}

## 选项
{options_joined}

## 题库声称的正确答案
{answer}

## 题库给出的解析
{explanation}

## 评估要点
1. 题目是否表述完整、有明确语义、可作答？
2. 声称的正确答案是否事实/技术上正确？
3. 在所有选项中，声称的答案是否是**唯一**正确的？（是否存在其他选项也对、或没有任何选项对）
4. 选项之间是否相互独立、无重复？
5. 题干、选项或解析是否有事实性错误？

## 决策原则
- 只有在你对「题目存在真实缺陷」**高度确信** 时，才输出 `delete`
- 如有疑问 → `keep`（宁可放过，不可错杀）
- 不要因为题目太难或表述偏学究气而判删

## 输出（仅 JSON）
{{
  "verdict": "keep" 或 "delete",
  "issues": ["如果 delete，列出具体问题（中文，简短）；如果 keep 则空数组"],
  "confidence": "high" 或 "medium" 或 "low"
}}
"""


def evaluate_question(client, q: Question, course_name: str) -> dict:
    """Send one question to DeepSeek for judgment. Returns the parsed JSON dict."""
    options_joined = "\n".join(q.options or []) if isinstance(q.options, list) else str(q.options)
    prompt = PROMPT_TEMPLATE.format(
        course_name=course_name,
        topic=q.topic,
        question_text=q.question_text,
        options_joined=options_joined,
        answer=q.answer,
        explanation=q.explanation,
    )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "你是严谨的考试题目审查员。只输出合法 JSON，不要任何额外文本。"},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=2000,
        **thinking_kwargs(effort="high"),
    )
    content = response.choices[0].message.content
    return json.loads(content)


class Command(BaseCommand):
    help = "Audit existing questions with DeepSeek; delete those with no/non-unique solution."

    def add_arguments(self, parser):
        parser.add_argument("--course", type=str, default=None,
                            help="Course id to audit (default: all courses)")
        parser.add_argument("--type", type=str, default="mcq",
                            choices=["mcq", "fill", "essay"],
                            help="Question type to audit (default: mcq — only MCQ supports auto-judging)")
        parser.add_argument("--apply", action="store_true",
                            help="Actually delete questions. Without this flag, runs in dry-run mode.")
        parser.add_argument("--dry-run", action="store_true",
                            help="(default) Just report; do not delete.")
        parser.add_argument("--limit", type=int, default=None,
                            help="Max number of questions to evaluate.")
        parser.add_argument("--concurrency", type=int, default=5,
                            help="Parallel LLM calls (default: 5).")
        parser.add_argument("--backup-dir", type=str,
                            default=str(BACKEND_DIR / "audit_backups"),
                            help="Where to write JSON backups of deleted questions.")

    def handle(self, *args, **opts):
        if not API_KEY:
            self.stderr.write(self.style.ERROR("DEEPSEEK_API_KEY not configured"))
            sys.exit(1)

        apply_changes = opts["apply"] and not opts["dry_run"]
        course_id = opts["course"]
        qtype = opts["type"]
        limit = opts["limit"]
        concurrency = opts["concurrency"]
        backup_dir = Path(opts["backup_dir"])

        # Build queryset
        qs = Question.objects.filter(question_type=qtype)
        if course_id:
            qs = qs.filter(course_id=course_id)
        if limit:
            qs = qs[:limit]
        questions = list(qs)

        if not questions:
            self.stdout.write(self.style.WARNING("No questions matched."))
            return

        # Resolve course names once
        course_names = {}
        for q in questions:
            if q.course_id not in course_names:
                cfg = get_course(q.course_id)
                course_names[q.course_id] = cfg.get("name", q.course_id) if cfg else q.course_id

        mode = "APPLY (will delete)" if apply_changes else "DRY-RUN (no deletes)"
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nAuditing {len(questions)} {qtype} questions  |  mode = {mode}  |  concurrency = {concurrency}"
        ))
        if apply_changes:
            backup_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(f"Backups → {backup_dir}\n")

        client = _get_deepseek_client(API_KEY)

        results = {
            "keep": 0,
            "delete": 0,
            "low_confidence_keep": 0,  # delete with low confidence → keep instead
            "errors": 0,
        }
        deletions = []  # list of (question, verdict_dict)
        errors = []
        t0 = time.time()
        done = 0
        total = len(questions)

        def worker(q: Question):
            try:
                verdict = evaluate_question(client, q, course_names.get(q.course_id, q.course_id))
                return q, verdict, None
            except Exception as e:
                return q, None, e

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(worker, q) for q in questions]
            for fut in as_completed(futures):
                q, verdict, err = fut.result()
                done += 1
                if err is not None:
                    results["errors"] += 1
                    errors.append((q, str(err)))
                    self.stdout.write(self.style.ERROR(
                        f"[{done:>3}/{total}] ERROR  id={q.id}  {err}"
                    ))
                    continue

                v = (verdict or {}).get("verdict", "keep")
                conf = (verdict or {}).get("confidence", "low")
                issues = (verdict or {}).get("issues", []) or []

                # Safety: only delete on HIGH confidence
                if v == "delete" and conf != "high":
                    results["low_confidence_keep"] += 1
                    self.stdout.write(self.style.WARNING(
                        f"[{done:>3}/{total}] KEEP*  id={q.id}  ({conf} confidence delete recommendation, ignored)"
                        f"  reason: {'; '.join(issues)[:120]}"
                    ))
                    continue

                if v == "delete":
                    results["delete"] += 1
                    deletions.append((q, verdict))
                    self.stdout.write(self.style.NOTICE(
                        f"[{done:>3}/{total}] DELETE id={q.id}  topic={q.topic}"
                        f"  reason: {'; '.join(issues)[:160]}"
                    ))
                else:
                    results["keep"] += 1
                    if done % 10 == 0:
                        self.stdout.write(f"[{done:>3}/{total}] KEEP   id={q.id}")

        elapsed = time.time() - t0

        # Persist deletions
        if apply_changes and deletions:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tag = course_id or "all"
            backup_path = backup_dir / f"audit_{tag}_{qtype}_{stamp}.jsonl"
            with backup_path.open("w", encoding="utf-8") as f:
                for q, verdict in deletions:
                    f.write(json.dumps({
                        "id": q.id,
                        "course_id": q.course_id,
                        "topic": q.topic,
                        "question_type": q.question_type,
                        "difficulty": q.difficulty,
                        "question_text": q.question_text,
                        "options": q.options,
                        "answer": q.answer,
                        "explanation": q.explanation,
                        "seed_question": q.seed_question,
                        "verdict": verdict,
                    }, ensure_ascii=False) + "\n")
            self.stdout.write(self.style.SUCCESS(f"\nBackup written: {backup_path}"))

            # Now actually delete
            ids_to_delete = [q.id for q, _ in deletions]
            Question.objects.filter(id__in=ids_to_delete).delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(ids_to_delete)} questions from DB."))

        # Final summary
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SUMMARY ==="))
        self.stdout.write(f"Mode:                    {mode}")
        self.stdout.write(f"Total evaluated:         {total}")
        self.stdout.write(f"Kept:                    {results['keep']}")
        self.stdout.write(f"Kept (low-conf rescue):  {results['low_confidence_keep']}")
        self.stdout.write(f"Marked for deletion:     {results['delete']}")
        self.stdout.write(f"Errors:                  {results['errors']}")
        self.stdout.write(f"Elapsed:                 {elapsed:.1f}s ({elapsed/total:.1f}s/question avg)")

        if not apply_changes and results["delete"] > 0:
            self.stdout.write(self.style.WARNING(
                f"\nDry-run complete. Re-run with --apply to actually delete {results['delete']} question(s)."
            ))

        if results["errors"]:
            self.stdout.write(self.style.WARNING(f"\n{len(errors)} questions errored — re-run to retry just those."))
