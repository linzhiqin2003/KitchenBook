"""把 AiLabConversation.token_usage JSON 里的累计 token 数迁移到
AiLabMessage 的 per-row 字段，方便新版 stats() 端点按 model 分桶统计。

策略（idempotent）：
  对每个 conversation，计算 token_usage 总数与该 conv 下 assistant 消息
  per-row token 之和的差值，把差额一次性记到该 conv 的最后一条 assistant
  消息上；并把它的 model_name 规整成 'deepseek-v4-flash'（部署前的唯一
  基座模型）。

  delta = conv.token_usage.totalXxx - SUM(message.xxx_tokens)
  · delta > 0 → backfill
  · delta <= 0 → 已迁移，跳过

执行：
    python manage.py backfill_ailab_token_usage          # dry-run
    python manage.py backfill_ailab_token_usage --apply  # 真写库
"""

from django.core.management.base import BaseCommand

from api.models import AiLabConversation


DEFAULT_MODEL = 'deepseek-v4-flash'  # 部署前唯一基座，归属合理


class Command(BaseCommand):
    help = 'Backfill per-message token counts from AiLabConversation.token_usage JSON.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='真写库（不传只 dry-run）',
        )

    def handle(self, *args, **opts):
        apply = bool(opts.get('apply'))
        backfilled = 0
        skipped_no_usage = 0
        skipped_no_msg = 0
        skipped_already = 0

        qs = AiLabConversation.objects.prefetch_related('messages').all()

        for conv in qs:
            usage = conv.token_usage or {}
            total_p = int(usage.get('totalPromptTokens') or 0)
            total_c = int(usage.get('totalCompletionTokens') or 0)
            total_k = int(usage.get('totalCacheTokens') or 0)

            if total_p == 0 and total_c == 0 and total_k == 0:
                skipped_no_usage += 1
                continue

            assistant_msgs = list(conv.messages.filter(role='assistant').order_by('created_at'))
            if not assistant_msgs:
                skipped_no_msg += 1
                continue

            recorded_p = sum(m.prompt_tokens for m in assistant_msgs)
            recorded_c = sum(m.completion_tokens for m in assistant_msgs)
            recorded_k = sum(m.cache_tokens for m in assistant_msgs)

            delta_p = max(0, total_p - recorded_p)
            delta_c = max(0, total_c - recorded_c)
            delta_k = max(0, total_k - recorded_k)

            if delta_p == 0 and delta_c == 0 and delta_k == 0:
                skipped_already += 1
                continue

            # 把 delta 一次性记到最后一条 assistant 消息上
            target = assistant_msgs[-1]
            old_model = target.model_name
            new_model = old_model if old_model and old_model not in ('', 'Hermes') else DEFAULT_MODEL

            self.stdout.write(
                f"conv={conv.id:<5} +p={delta_p:<8} +c={delta_c:<6} +k={delta_k:<8} "
                f"→ msg={target.id} model={old_model!r} → {new_model!r}"
            )

            if apply:
                target.prompt_tokens = target.prompt_tokens + delta_p
                target.completion_tokens = target.completion_tokens + delta_c
                target.cache_tokens = target.cache_tokens + delta_k
                target.model_name = new_model
                target.save(update_fields=[
                    'prompt_tokens', 'completion_tokens', 'cache_tokens', 'model_name',
                ])

            backfilled += 1

        prefix = '' if apply else '[dry-run] '
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}done — backfilled={backfilled} "
            f"skipped(no_usage={skipped_no_usage}, no_msg={skipped_no_msg}, already={skipped_already})"
        ))
        if not apply and backfilled > 0:
            self.stdout.write(self.style.WARNING(
                "Run with --apply to actually write the changes."
            ))
