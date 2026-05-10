import json
from datetime import datetime

from django.conf import settings

from common.deepseek_models import CHAT_MODEL, get_client, non_thinking_kwargs

from .vlm import _build_prompt, _strip_json_fences


CHAT_INSTRUCTIONS = """
【重要】你现在是对话模式的智能记账助手，不是图片识别模式。

## 工作流程
1. 用户用自然语言描述购物经历
2. 分析用户提供的信息，判断是否足够生成完整账单
3. 如果关键信息缺失，用简短友好的中文向用户提问
4. 当信息充足时，直接输出符合上述格式的纯 JSON

## 关键信息（缺一不可，务必逐项确认）
- **商店名称**：在哪家店/平台买的（非常重要，必须明确）
- **商品清单**：买了哪些东西
- **商品价格**：每样东西的单价是多少，买了几件；如果用户只给了某商品的总花费也可以
- **小计**：subtotal 由各商品 total_price 求和得到（系统会自动按 subtotal + tax - discount 派生最终总价，无需输出 total）

## 可选但值得确认的信息
- **购买日期**：如果用户没提到，询问一次；如果用户说不记得或不想填，purchased_at 设为 null
- **品牌**：如果能从描述中推断就填，否则留空

## 特别注意
- 如果用户只说了"买了XXX"但没说价格，一定要追问每样东西花了多少钱
- 如果用户没说在哪买的，一定要追问商店名称
- 单价(unit_price)和总价(total_price)都要尽量填写：total_price = unit_price × quantity

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
- 如果用户说"昨天""今天""前天""刚才"等相对日期/时间，根据当前时间推算：当前时间是 {now}
- 如果用户没提到小计但有各商品价格，自动计算 subtotal；不要输出 total（系统会自动派生）
""".strip()


def _build_chat_prompt() -> str:
    """Build system prompt for conversational receipt generation."""
    base = _build_prompt()
    instructions = CHAT_INSTRUCTIONS.format(now=datetime.now().strftime("%Y-%m-%d %H:%M"))
    return base + "\n\n" + instructions


def chat_or_generate(messages: list[dict]) -> dict:
    """Multi-turn conversation for receipt generation, backed by deepseek-v4-flash.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}

    Returns:
        {"type": "chat", "message": "..."} — AI asks a question
        {"type": "receipt", "content": "..."} — AI outputs receipt JSON
    """
    api_key = getattr(settings, "DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY")

    client = get_client(api_key)
    if client is None:
        raise RuntimeError("Failed to initialize DeepSeek client")

    system_prompt = _build_chat_prompt()
    api_messages = [{"role": "system", "content": system_prompt}] + messages

    # v4-flash 默认开启 thinking，会消耗 reasoning tokens 并可能返回空 content；
    # 这里是快速 chat 场景，必须显式 disable。
    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=api_messages,
        temperature=0.3,
        **non_thinking_kwargs(),
    )
    msg = completion.choices[0].message
    raw = (msg.content or "").strip()

    # Try to detect if the response is receipt JSON
    cleaned = _strip_json_fences(raw)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "items" in parsed:
            return {"type": "receipt", "content": cleaned}
    except (json.JSONDecodeError, TypeError):
        pass

    return {"type": "chat", "message": raw}
