import json
import os
from datetime import date

from cerebras.cloud.sdk import Cerebras

from .doubao import _build_prompt, _strip_json_fences


CHAT_INSTRUCTIONS = """
【重要】你现在是对话模式的智能记账助手，不是图片识别模式。

## 工作流程
1. 用户用自然语言描述购物经历
2. 分析用户提供的信息，判断是否足够生成完整账单
3. 如果关键信息缺失，用简短友好的中文向用户提问
4. 当信息充足时，直接输出符合上述格式的纯 JSON

## 关键信息（缺一不可）
- **商店名称**：在哪里买的
- **商品清单**：买了什么东西
- **商品价格**：每样东西花了多少钱

## 可选但值得确认的信息
- **购买日期**：如果用户没提到，询问一次；如果用户说不记得或不想填，purchased_at 设为 null
- **品牌**：如果能从描述中推断就填，否则留空

## 提问规则
- 一次最多问 2-3 个问题，用简短自然的中文
- 不要输出 JSON，只输出纯文本
- 不要重复问已经知道的信息
- 语气友好简洁，像朋友聊天

## 生成规则
- 当有足够信息时，直接输出纯 JSON，不要加任何其他文字，不要用 ```json 包裹
- is_receipt 设为 true
- confidence 设为 0.95
- 如果用户没提到日期且不想填，purchased_at 设为 null
- 如果用户说"昨天""今天""前天"等相对日期，根据当前日期推算：当前日期是 {today}
- 如果用户没提到总价但有各商品价格，自动计算 subtotal 和 total
""".strip()


def _build_chat_prompt() -> str:
    """Build system prompt for conversational receipt generation."""
    base = _build_prompt()
    instructions = CHAT_INSTRUCTIONS.format(today=date.today().isoformat())
    return base + "\n\n" + instructions


def chat_or_generate(messages: list[dict]) -> dict:
    """Multi-turn conversation for receipt generation.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}

    Returns:
        {"type": "chat", "message": "..."} — AI asks a question
        {"type": "receipt", "content": "..."} — AI outputs receipt JSON
    """
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing CEREBRAS_API_KEY")

    client = Cerebras(api_key=api_key)
    system_prompt = _build_chat_prompt()

    api_messages = [{"role": "system", "content": system_prompt}] + messages

    completion = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=api_messages,
        temperature=0.3,
    )
    raw = completion.choices[0].message.content.strip()

    # Try to detect if the response is receipt JSON
    cleaned = _strip_json_fences(raw)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "items" in parsed:
            return {"type": "receipt", "content": cleaned}
    except (json.JSONDecodeError, TypeError):
        pass

    return {"type": "chat", "message": raw}
