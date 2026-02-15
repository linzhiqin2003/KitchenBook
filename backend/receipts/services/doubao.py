import base64
import io
import json as _json
import os
import time
from typing import Any
import requests
from PIL import Image

PROMPT_TEMPLATE = """
你是一个收据解析助手。请从图片中识别超市/商店收据，严格输出纯 JSON（不要任何额外文本，不要用 ```json 等 Markdown 代码块包裹）。
JSON 结构要求：
{{
  "merchant": "商店名(不含地址)",
  "address": "商店地址(如未知可空)",
  "purchased_at": "ISO 8601 时间(如未知可空)",
  "currency": "GBP",
  "subtotal": 12.34,
  "tax": 0.0,
  "discount": 0.0,
  "total": 12.34,
  "items": [
    {{
      "main_category": "主类",
      "sub_category": "子类",
      "name": "商品名",
      "brand": "品牌(可空)",
      "quantity": 1,
      "unit": "单位",
      "unit_price": 3.50,
      "total_price": 3.50,
      "tags": ["可选标签"],
      "confidence": 0.90
    }}
  ]
}}
如果图片中不包含收据/发票/小票，请输出：
{{"is_receipt": false, "reason": "简要说明图片内容"}}

如果是收据，在上述 JSON 基础上加上 "is_receipt": true。

说明：
- 必须是有效 JSON
- 金额使用数字
- 类目尽量细分：主类-子类-商品名
- 【重要】必须列出收据上的每一个商品，严禁遗漏！即使无法确定分类，也要输出该商品并将 main_category 设为"其他"

商店名(merchant)字段规范：
{merchant_instruction}

主类(main_category)字段规范：
{categories_instruction}

单位(unit)字段规范：
- 只能从以下值中选择：个, 包, 袋, 盒, 瓶, 罐, 桶, 杯, 根, 条, 块, 片, 只, 把, 份, 串, 组, 打, 支, 卷, 升, 毫升, 千克, 克, 斤, 磅, 盘, 碗
- 如果收据上标注了净含量/规格(如 130g, 310ml, 500ml)，填入 tags 字段而非 unit 字段
- 如果无法判断单位，默认使用"个"
- 禁止使用英文单位(pack/bottle/kg等)，统一使用中文

日期(purchased_at)字段规范：
- 仔细查看收据/发票上是否印有日期(购买日期、交易日期、打印日期等)
- 如果能看到日期，提取并转为 ISO 8601 格式填入 purchased_at
- 如果收据上没有任何日期信息，purchased_at 设为 null

品牌(brand)字段规范：
- 只有在收据上能明确看到品牌名时才填写(如"李锦记"、"王致和"、"功夫")
- 如果收据上没有标注品牌，brand 设为 null，不要猜测或用英文商品代码充当品牌
- 品牌名使用中文，如果原文是英文且有通用中文译名则翻译

商品名(name)与子类(sub_category)识别规范：
- 很多收据同时印有中文名和英文名，以中文名为准来判断商品和子类
- 【重要】必须把中文商品名作为一个整体来理解，严禁拆字归类！
  错误示例：
  × "咸蛋黄油条" → 拆成"咸/盐" → 归为调味品（错！这是一种油炸面食零食）
  × "红油豆瓣酱" → 只看"油" → 归为食用油（错！这是酱料调味品）
  正确做法：
  √ "咸蛋黄油条" → 整体理解为"咸蛋黄味的油条" → 零食糕点
  √ "红油豆瓣酱" → 整体理解为"豆瓣酱" → 调味品
- 分类时先理解完整商品名的含义，再决定主类和子类

语言规范：
- main_category、sub_category、name、brand、unit 等字段统一使用中文
- 英文收据上的商品名需翻译为中文商品通用名称
- 如果收据同时有中英文，以中文为准识别商品，忽略英文
- merchant(商店名)和 address(地址)保留原文，不翻译
- tags 中的规格信息保留原始标注(如 "130g", "310ml")

多图说明：
- 如果收到多张图片，它们属于同一张收据（正反面或分段拍摄）
- 请综合所有图片信息，合并去重后输出一份完整的收据 JSON
- 商品不要重复列出，如果多张图片有重叠部分请去重
""".strip()

_MERCHANTS_WITH_EXISTING = (
    "- 系统中已有以下商店：【{existing}】\n"
    "- 如果收据上的商店名与上述某个商店是同一家（仅大小写、空格、分店后缀等差异），请使用已有名称\n"
    "- 如果是全新的商店，保留收据原文"
)

_MERCHANTS_NO_EXISTING = (
    "- 保留收据上的商店原文，不翻译"
)

_CATEGORIES_STANDARD = (
    "- 必须从以下标准主类中选择，禁止自创主类：\n"
    "  · 生鲜肉类 — 猪牛羊鸡鸭鱼虾等生鲜肉、肉卷、肉丸\n"
    "  · 蔬菜水果 — 新鲜蔬菜、叶菜、根茎、菌菇(金针菇/香菇等)、新鲜水果\n"
    "  · 粮油副食 — 米、面、面条、食用油、干货(木耳/腐竹/粉丝等)\n"
    "  · 调味品 — 酱油、醋、盐、糖、料酒、酱料、调料包、火锅底料\n"
    "  · 饮料 — 水、茶饮(加多宝/王老吉等)、果汁、碳酸饮料、咖啡\n"
    "  · 乳制品 — 牛奶、酸奶、奶酪、奶油\n"
    "  · 速食食品 — 方便面、冷冻水饺、速冻食品、即食品\n"
    "  · 零食糕点 — 饼干、糖果、坚果、面包、蛋糕、膨化食品\n"
    "  · 豆制品 — 豆腐、豆干、豆浆、腐乳\n"
    "  · 酒类 — 白酒、啤酒、葡萄酒、黄酒\n"
    "  · 日用品 — 纸巾、洗涤剂、清洁用品、个人护理\n"
    "  · 其他 — 以上都无法归类时使用\n"
    "- 注意：调味品是调味品，不是干货；茶饮是饮料；新鲜菌菇是蔬菜水果，不是干货"
)


def _build_prompt() -> str:
    """Build the system prompt with standard categories and existing merchants."""
    from receipts.models import Receipt

    cat_instruction = _CATEGORIES_STANDARD

    merchant_names = list(
        Receipt.objects
        .exclude(merchant="")
        .values_list("merchant", flat=True)
        .distinct()
        .order_by("merchant")
    )
    if merchant_names:
        merchant_instruction = _MERCHANTS_WITH_EXISTING.format(existing="、".join(merchant_names))
    else:
        merchant_instruction = _MERCHANTS_NO_EXISTING

    return PROMPT_TEMPLATE.format(
        categories_instruction=cat_instruction,
        merchant_instruction=merchant_instruction,
    )


def _load_env(name: str, fallback: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    return fallback


def _compress_image(image_path: str, max_long_edge: int = 2048, max_bytes: int = 1_500_000) -> bytes:
    """Compress image while preserving quality as much as possible."""
    img = Image.open(image_path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_long_edge:
        ratio = max_long_edge / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    for q in (95, 90, 85, 78, 70):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        if buf.tell() <= max_bytes:
            return buf.getvalue()
    return buf.getvalue()


def _encode_image_to_data_url(image_path: str) -> str:
    compressed = _compress_image(image_path)
    encoded = base64.b64encode(compressed).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


# ─── Provider abstraction ───


def _get_provider() -> str:
    """Determine which provider to use: 'openrouter' or 'ark'."""
    if _load_env("OPENROUTER_API_KEY"):
        return "openrouter"
    return "ark"


def _build_payload(image_paths: str | list[str]) -> tuple[dict, dict]:
    """Build the API payload and connection info. Accepts single path or list of paths."""
    provider = _get_provider()
    prompt = _build_prompt()

    if isinstance(image_paths, str):
        image_paths = [image_paths]

    user_content: list[dict] = []
    if len(image_paths) == 1:
        user_content.append({"type": "text", "text": "请解析这张收据"})
    else:
        user_content.append({
            "type": "text",
            "text": f"以下 {len(image_paths)} 张图片属于同一张收据（可能是正反面或分段拍摄），请综合所有图片解析出一份完整账单。",
        })

    for path in image_paths:
        image_url = _encode_image_to_data_url(path)
        user_content.append({"type": "image_url", "image_url": {"url": image_url}})

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]

    if provider == "openrouter":
        api_key = _load_env("OPENROUTER_API_KEY")
        model = _load_env("OPENROUTER_MODEL", "qwen/qwen3-vl-32b-instruct")
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://receipt-analysis.local",
            "X-Title": "ReceiptAnalysis",
        }
        url = "https://openrouter.ai/api/v1/chat/completions"
    else:
        api_key = _load_env("ARK_API_KEY") or _load_env("DOUBAO_API_KEY")
        base_url = _load_env("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        model_id = _load_env("ARK_MODEL_ID") or _load_env("DOUBAO_MODEL_ID")
        if not api_key:
            raise RuntimeError("Missing ARK_API_KEY / DOUBAO_API_KEY")
        if not model_id:
            raise RuntimeError("Missing ARK_MODEL_ID / DOUBAO_MODEL_ID")
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.2,
            "thinking": {"type": "enabled", "budget_tokens": 4096},
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = f"{base_url.rstrip('/')}/chat/completions"

    return payload, {"url": url, "headers": headers}


def _strip_json_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) if present."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
    if s.endswith("```"):
        s = s.rsplit("\n", 1)[0] if "\n" in s else s[:-3]
    return s.strip()


def analyze_receipt(image_paths: str | list[str]) -> tuple[str, dict[str, Any]]:
    payload, conn = _build_payload(image_paths)
    response = requests.post(conn["url"], json=payload, headers=conn["headers"], timeout=360)
    response.raise_for_status()
    data = response.json()
    content = _strip_json_fences(data["choices"][0]["message"]["content"])
    return content, data


def analyze_receipt_stream(image_paths: str | list[str]):
    """Stream analysis, yielding phase events: thinking / generating / done."""
    payload, conn = _build_payload(image_paths)
    payload["stream"] = True

    response = requests.post(
        conn["url"], json=payload, headers=conn["headers"],
        timeout=360, stream=True,
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    phase = "thinking"
    content_parts: list[str] = []
    thinking_buf: list[str] = []
    generating_buf: list[str] = []
    last_yield_time = time.monotonic()
    BATCH_INTERVAL = 0.3

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data: "):
            continue
        data_str = raw_line[6:]
        if data_str.strip() == "[DONE]":
            break
        try:
            chunk = _json.loads(data_str)
        except _json.JSONDecodeError:
            continue

        delta = chunk.get("choices", [{}])[0].get("delta", {})

        # thinking phase (reasoning_content — Ark/Qwen thinking mode)
        reasoning = delta.get("reasoning_content") or delta.get("reasoning", "")
        if reasoning:
            if phase != "thinking":
                phase = "thinking"
            thinking_buf.append(reasoning)

        # generating phase (content)
        content = delta.get("content")
        if content:
            if phase != "generating":
                phase = "generating"
                if thinking_buf:
                    yield {"phase": "thinking", "text": "".join(thinking_buf)}
                    thinking_buf.clear()
            generating_buf.append(content)
            content_parts.append(content)

        # Batch yield at intervals
        now = time.monotonic()
        if now - last_yield_time >= BATCH_INTERVAL:
            if thinking_buf:
                yield {"phase": "thinking", "text": "".join(thinking_buf)}
                thinking_buf.clear()
            if generating_buf:
                yield {"phase": "generating", "text": "".join(generating_buf)}
                generating_buf.clear()
            last_yield_time = now

    # Flush remaining
    if thinking_buf:
        yield {"phase": "thinking", "text": "".join(thinking_buf)}
    if generating_buf:
        yield {"phase": "generating", "text": "".join(generating_buf)}

    final_content = _strip_json_fences("".join(content_parts))
    yield {"phase": "done", "content": final_content}
