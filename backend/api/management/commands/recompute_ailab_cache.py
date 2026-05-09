"""把 Hermes _run_agent bug 时期遗留的 cache_tokens=0 反推回真实值。

背景:
  patch 17 之前，api_server.py::_run_agent 在构造给前端的 usage dict 时
  漏读了 session_cache_read/write_tokens —— SSE finish chunk 的 cache_tokens
  字段永远是 0，DB 跟着写 0。这导致 cost 估算长期按 upper bound 算。

修复后 (patch 17):
  新会话的 cache_tokens 从上游真实流过来。这个 command 只处理历史的、
  cache_tokens=0 但 prompt_tokens>0 的 assistant message。

按 turn 估算 cache:
  cache_tokens ≈ max(0, prompt_tokens - new_content_in_turn)

  其中 new_content_in_turn 包含:
    · 该轮 user message 的 content
    · assistant 的 reasoning（思考链）
    · 所有 sub_turn 的 tool_call.result（数据库里有）
    · tool_call.arguments 估算 (~result 5%)
    · sub_turn 元信息（name / id）
    · assistant 最终 content
    · (会话首条) system prompt + tools (实测约 13K tok)

跳过:
  · cache_tokens 已有值（真实上游数据，不覆盖）
  · prompt_tokens=0（无 LLM 调用，比如纯 user 消息）

执行:
    python manage.py recompute_ailab_cache              # dry-run
    python manage.py recompute_ailab_cache --apply      # 真写库
    python manage.py recompute_ailab_cache --conv 55    # 只处理某会话
"""

import json

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import AiLabConversation, AiLabMessage


# Hermes system prompt + tools description (实测 2026-05-09 patch17 SSE chunk
# breakdown.total_local ≈ 13K tok：identity+tools+memory+skills+...). 这是会话
# 首次 cache write 的内容，之后每个 turn 都会作为 cache 命中重读。
SYSTEM_PROMPT_TOK = 13000
# tool call arguments 没存到 sub_turns（前端只存 name / id / result）。按 result
# 大小 5% 估算（terminal/write_file 等命令的 args 通常远短于 result）。
TOOL_ARGS_RATIO = 0.05
TOOL_ARGS_FLOOR = 20  # arguments 至少占这么多 token（含 JSON 包裹）


def _load_tokenizer():
    try:
        import tiktoken
    except ImportError:
        return None
    return tiktoken.get_encoding("cl100k_base")


class Command(BaseCommand):
    help = "Backfill estimated cache_tokens for assistant messages where Hermes dropped them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="真写库（不传只 dry-run，默认显示统计）",
        )
        parser.add_argument(
            "--conv",
            type=int,
            default=None,
            help="只处理某 conversation_id（用于针对性验证）",
        )

    def handle(self, *args, **opts):
        enc = _load_tokenizer()
        if enc is None:
            self.stderr.write(
                "tiktoken 未安装。请先 `pip install tiktoken` 再跑此命令。"
            )
            return

        def n_tok(s: str) -> int:
            return len(enc.encode(s)) if s else 0

        apply = bool(opts.get("apply"))
        only_conv = opts.get("conv")

        # 哪些 conversation 有需要处理的 message
        candidates = AiLabConversation.objects.filter(
            messages__role="assistant",
            messages__cache_tokens=0,
            messages__prompt_tokens__gt=0,
        ).distinct().order_by("id")
        if only_conv:
            candidates = candidates.filter(id=only_conv)

        per_conv = []
        total_msgs = 0
        total_target_prompt = 0
        total_new_cache = 0

        for conv in candidates:
            msgs = list(
                AiLabMessage.objects
                .filter(conversation=conv)
                .order_by("created_at")
            )

            first_assistant_seen = False
            pending_user_content = ""
            updates = []

            for m in msgs:
                if m.role == "user":
                    if pending_user_content:
                        pending_user_content += "\n"
                    pending_user_content += (m.content or "")
                    continue

                if m.role != "assistant":
                    continue

                prompt = int(m.prompt_tokens or 0)
                cache = int(m.cache_tokens or 0)
                if prompt == 0:
                    pending_user_content = ""
                    first_assistant_seen = True
                    continue
                if cache > 0:
                    # 已有真实数据，不覆盖
                    pending_user_content = ""
                    first_assistant_seen = True
                    continue

                new_in_turn = n_tok(pending_user_content)
                new_in_turn += n_tok(m.content or "")
                new_in_turn += n_tok(m.reasoning or "")

                for st in (m.sub_turns or []):
                    if not isinstance(st, dict):
                        continue
                    tc = st.get("toolCall")
                    if not tc:
                        continue
                    r = tc.get("result") or ""
                    r_str = r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)
                    r_tok = n_tok(r_str)
                    new_in_turn += r_tok
                    # tool args (没存) 估算
                    new_in_turn += max(TOOL_ARGS_FLOOR, int(r_tok * TOOL_ARGS_RATIO))
                    # name + id meta
                    new_in_turn += n_tok(json.dumps(
                        {"name": tc.get("name"), "id": tc.get("id")},
                        ensure_ascii=False,
                    ))

                if not first_assistant_seen:
                    new_in_turn += SYSTEM_PROMPT_TOK
                    first_assistant_seen = True

                # cache = prompt 累加 - 这一 turn 真实新增（multi-step 内部
                # 反复读的 prefix 全是 cache）
                estimated_cache = max(0, prompt - new_in_turn)
                estimated_cache = min(estimated_cache, prompt)  # 防御

                updates.append((m.id, estimated_cache, prompt, new_in_turn))
                total_msgs += 1
                total_target_prompt += prompt
                total_new_cache += estimated_cache
                pending_user_content = ""

            if updates:
                conv_cache_sum = sum(u[1] for u in updates)
                conv_prompt_sum = sum(u[2] for u in updates)
                hit_pct = (100 * conv_cache_sum // conv_prompt_sum) if conv_prompt_sum else 0
                per_conv.append((conv.id, len(updates), conv_prompt_sum, conv_cache_sum, hit_pct))

                if apply:
                    with transaction.atomic():
                        for mid, cache_val, _prompt, _newin in updates:
                            AiLabMessage.objects.filter(id=mid).update(cache_tokens=cache_val)

        self.stdout.write(f"Processed {len(per_conv)} conversations, {total_msgs} messages")
        self.stdout.write(f"Target prompt_tokens (sum):   {total_target_prompt:_}")
        self.stdout.write(self.style.SUCCESS(
            f"Estimated cache writes (sum): {total_new_cache:_}  "
            f"({100*total_new_cache//max(total_target_prompt,1)}% hit rate)"
        ))
        if per_conv:
            self.stdout.write("\nPer-conversation:")
            self.stdout.write(f"  {'conv':>5}  {'msgs':>5}  {'prompt':>14}  {'cache':>14}  {'hit%':>5}")
            for cid, count, p_sum, c_sum, pct in per_conv[:25]:
                self.stdout.write(f"  {cid:>5}  {count:>5}  {p_sum:>14_}  {c_sum:>14_}  {pct:>4}%")
            if len(per_conv) > 25:
                self.stdout.write(f"  ... ({len(per_conv)-25} more)")

        if not apply:
            self.stdout.write(self.style.NOTICE(
                f"\n[DRY RUN] add --apply to write {total_msgs} cache_tokens updates"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nApplied {total_msgs} updates."))
