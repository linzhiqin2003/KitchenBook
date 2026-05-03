"""Batch-translate KnowledgePoint content to Chinese using DeepSeek."""
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from questions.models import KnowledgePoint
from common.deepseek_models import CHAT_MODEL, get_client, non_thinking_kwargs

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Command(BaseCommand):
    help = "Translate KnowledgePoint title/definition/details to Chinese"

    def add_arguments(self, parser):
        parser.add_argument("--course", default="software-engineering")
        parser.add_argument("--topic", default=None, help="Specific topic to translate")
        parser.add_argument("--force", action="store_true", help="Re-translate already translated")

    def handle(self, *args, **options):
        client = get_client(os.getenv("DEEPSEEK_API_KEY"))
        if not client:
            self.stderr.write("DEEPSEEK_API_KEY not set")
            return

        qs = KnowledgePoint.objects.filter(course_id=options["course"])
        if options["topic"]:
            qs = qs.filter(topic=options["topic"])
        if not options["force"]:
            qs = qs.filter(translations={})

        topics = {}
        for kp in qs.order_by("topic", "sequence"):
            topics.setdefault(kp.topic, []).append(kp)

        self.stdout.write(f"Topics to translate: {len(topics)}, total points: {sum(len(v) for v in topics.values())}")

        for topic, points in topics.items():
            self.stdout.write(f"\n  [{topic}] {len(points)} points...")
            batch = []
            for kp in points:
                batch.append({
                    "id": kp.id,
                    "title": kp.title,
                    "definition": kp.definition,
                    "details": kp.details or [],
                })

            prompt = (
                "Translate the following knowledge points from English to Chinese. "
                "Return a JSON array with the same structure. For each item, provide:\n"
                '- "id": same id\n'
                '- "title_cn": Chinese title\n'
                '- "definition_cn": Chinese definition\n'
                '- "details_cn": array of Chinese translations for each detail\n\n'
                "Be concise and accurate. Use technical terms appropriately.\n\n"
                f"```json\n{json.dumps(batch, ensure_ascii=False, indent=2)}\n```"
            )

            try:
                resp = client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4000,
                    **non_thinking_kwargs(),
                )
                raw = resp.choices[0].message.content.strip()
                # Extract JSON from markdown code block if present
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

                translations = json.loads(raw)
                kp_map = {kp.id: kp for kp in points}

                for item in translations:
                    kp = kp_map.get(item.get("id"))
                    if not kp:
                        continue
                    kp.translations = {
                        "title_cn": item.get("title_cn", ""),
                        "definition_cn": item.get("definition_cn", ""),
                        "details_cn": item.get("details_cn", []),
                    }
                    kp.save(update_fields=["translations"])

                self.stdout.write(self.style.SUCCESS(f"    ✓ {len(translations)} translated"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"    ✗ {topic}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nDone."))
