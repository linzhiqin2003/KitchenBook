import base64
import io
import os
from typing import Any
import requests
from PIL import Image

PROMPT_TEMPLATE = """
你是一个收据解析助手。请从图片中识别超市/商店收据，严格输出 JSON（不要任何额外文本）。
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

语言规范：
- main_category、sub_category、name、brand、unit 等字段统一使用中文
- 英文收据上的商品名需翻译为中文商品通用名称
- merchant(商店名)和 address(地址)保留原文，不翻译
- tags 中的规格信息保留原始标注(如 "130g", "310ml")
""".strip()

_MERCHANTS_WITH_EXISTING = (
    "- 系统中已有以下商店：【{existing}】\n"
    "- 如果收据上的商店名与上述某个商店是同一家（仅大小写、空格、分店后缀等差异），请使用已有名称\n"
    "- 如果是全新的商店，保留收据原文"
)

_MERCHANTS_NO_EXISTING = (
    "- 保留收据上的商店原文，不翻译"
)

_CATEGORIES_WITH_EXISTING = (
    "- 系统中已有以下主类：【{existing}】\n"
    "- 请优先从上述已有主类中选择，保持分类一致性\n"
    "- 只有当商品确实不属于任何已有主类时，才可以使用新的主类名称\n"
    "- 新主类应简洁、通用，使用中文"
)

_CATEGORIES_NO_EXISTING = (
    "- 主类应简洁、通用，使用中文（如：食品、饮料、日用品、蔬菜水果、肉类、乳制品等）"
)


def _build_prompt() -> str:
    """Build the system prompt with existing categories and merchants injected."""
    from receipts.models import CategoryMain, Receipt

    # Existing categories
    cat_names = list(CategoryMain.objects.order_by("name").values_list("name", flat=True))
    if cat_names:
        cat_instruction = _CATEGORIES_WITH_EXISTING.format(existing="、".join(cat_names))
    else:
        cat_instruction = _CATEGORIES_NO_EXISTING

    # Existing merchants (distinct, non-empty)
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
    """Compress image while preserving quality as much as possible.

    Strategy: only resize if exceeding max_long_edge, then progressively
    lower JPEG quality only if the result still exceeds max_bytes.
    """
    img = Image.open(image_path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_long_edge:
        ratio = max_long_edge / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    # Try quality from high to low until under max_bytes
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


def _build_payload(image_path: str) -> tuple[dict, dict]:
    """Build the API payload and headers for receipt analysis."""
    api_key = _load_env("ARK_API_KEY") or _load_env("DOUBAO_API_KEY")
    base_url = _load_env("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model_id = _load_env("ARK_MODEL_ID") or _load_env("DOUBAO_MODEL_ID")

    if not api_key:
        raise RuntimeError("Missing ARK_API_KEY / DOUBAO_API_KEY")
    if not model_id:
        raise RuntimeError("Missing ARK_MODEL_ID / DOUBAO_MODEL_ID (model endpoint ID)")

    prompt = _build_prompt()
    image_url = _encode_image_to_data_url(image_path)
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请解析这张收据"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        "temperature": 0.2,
        "thinking": {"type": "enabled", "budget_tokens": 4096},
    }

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"{base_url.rstrip('/')}/chat/completions"
    return payload, {"url": url, "headers": headers}


def analyze_receipt(image_path: str) -> tuple[str, dict[str, Any]]:
    payload, conn = _build_payload(image_path)
    response = requests.post(conn["url"], json=payload, headers=conn["headers"], timeout=360)
    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"]
    return content, data


def analyze_receipt_stream(image_path: str):
    """Stream analysis, yielding phase events: thinking / generating / done / error."""
    import json as _json

    payload, conn = _build_payload(image_path)
    payload["stream"] = True

    response = requests.post(
        conn["url"], json=payload, headers=conn["headers"],
        timeout=360, stream=True,
    )
    response.raise_for_status()

    phase = "thinking"
    content_parts: list[str] = []

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

        # thinking phase: reasoning_content present
        if delta.get("reasoning_content"):
            if phase != "thinking":
                phase = "thinking"
            yield {"phase": "thinking"}

        # generating phase: content present
        if delta.get("content"):
            if phase != "generating":
                phase = "generating"
                yield {"phase": "generating"}
            content_parts.append(delta["content"])

    final_content = "".join(content_parts)
    yield {"phase": "done", "content": final_content}
