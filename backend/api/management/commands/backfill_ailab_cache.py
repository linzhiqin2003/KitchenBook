"""清掉历史上由 _estimate_session_cache_tokens hook 写入的 cache_tokens。

那个 hook 在 multi-step agent 场景下用了错误的估算公式
(cache = min(prev_assistant.prompt_tokens, current.prompt_tokens))，
把"上一轮 prompt 总累加值"当作"本轮 cache 命中上限"，跨多次内部 LLM
调用累加之后高度失真，结果是 cost 严重低估。

判定逻辑：
  对每个会话遍历 assistant message（按 created_at 升序），如果
  current.cache_tokens == min(prev.prompt_tokens, current.prompt_tokens)
  且 cache_tokens > 0，认为是 hook 写入的噪声 → 重置为 0。

不动的场景：
  · 首条 assistant（没有 prev）—— 这种 cache>0 必然是上游真实值
  · cache_tokens != 估算公式 —— 真实上游数据保留

执行：
    python manage.py backfill_ailab_cache          # dry-run
    python manage.py backfill_ailab_cache --apply  # 真写库
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import AiLabConversation, AiLabMessage


class Command(BaseCommand):
    help = 'Reset hook-estimated cache_tokens back to 0 (keep real upstream data).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='真写库（不传只 dry-run，默认显示统计）',
        )

    def handle(self, *args, **opts):
        apply = bool(opts.get('apply'))

        total_assistant = 0
        total_nonzero_cache = 0
        to_reset_ids = []
        kept_real = 0

        for conv in AiLabConversation.objects.filter(messages__role='assistant').distinct():
            msgs = list(
                AiLabMessage.objects
                .filter(conversation=conv, role='assistant')
                .order_by('created_at')
                .values('id', 'prompt_tokens', 'cache_tokens')
            )
            prev = None
            for m in msgs:
                total_assistant += 1
                cache = int(m['cache_tokens'] or 0)
                if cache > 0:
                    total_nonzero_cache += 1
                    if prev is not None:
                        prev_p = int(prev['prompt_tokens'] or 0)
                        cur_p = int(m['prompt_tokens'] or 0)
                        if cache == min(prev_p, cur_p):
                            to_reset_ids.append(m['id'])
                        else:
                            kept_real += 1
                    else:
                        # 首条 assistant：没有 prev，cache 不可能是 hook 估算的
                        kept_real += 1
                prev = m

        self.stdout.write(f'total assistant messages   : {total_assistant}')
        self.stdout.write(f'  cache_tokens > 0         : {total_nonzero_cache}')
        self.stdout.write(self.style.WARNING(
            f'  match hook estimate (drop): {len(to_reset_ids)}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'  real upstream data (keep) : {kept_real}'
        ))

        if not to_reset_ids:
            self.stdout.write('Nothing to reset.')
            return

        if not apply:
            self.stdout.write(self.style.NOTICE(
                f'\n[DRY RUN] add --apply to reset {len(to_reset_ids)} rows to cache_tokens=0'
            ))
            return

        with transaction.atomic():
            updated = AiLabMessage.objects.filter(id__in=to_reset_ids).update(cache_tokens=0)
        self.stdout.write(self.style.SUCCESS(f'\nReset {updated} rows.'))
