import base64
import io
import json as _json
import os
import time
from typing import Any
import requests
from PIL import Image

PROMPT_TEMPLATE = """
<task>
你是购物凭证解析助手。从图片中识别以下任意一种购物凭证并提取结构化数据：
- 实体收据/小票/发票（超市、商店、餐厅等）
- 网购订单截图（淘宝、京东、拼多多、Amazon、外卖平台等的订单详情/订单列表）
- 电子收据截图（邮件收据、App 内收据等）
输出要求：严格输出纯 JSON，不要任何额外文本，不要用 ```json 等 Markdown 代码块包裹。
</task>

<non_receipt>
首先判断图片是否包含购物/消费信息（实体收据、网购订单、电子收据等均可）。
若图片与购物/消费完全无关，立即输出以下格式并停止：
{{"is_receipt": false, "reason": "简要说明图片内容"}}
</non_receipt>

<output_schema>
若图片包含购物凭证，输出以下结构（所有字段必须存在，未知字段填 null）：
{{
  "is_receipt": true,
  "merchant": "商店名（不含地址）",
  "address": "商店地址，未知填 null",
  "purchased_at": "ISO 8601 格式时间，未知填 null",
  "currency": "从收据识别，如 GBP/CNY/USD，未知填 GBP",
  "subtotal": 12.34,
  "tax": 0.0,
  "discount": 0.0,
  "total": 12.34,
  "items": [
    {{
      "main_category": "主类（见规则）",
      "name": "商品中文名",
      "brand": "品牌，未知填 null",
      "quantity": 1,
      "unit": "单位（见规则）",
      "unit_price": 3.50,
      "discount": 0,
      "tags": ["规格信息，如 430g / 500ml"],
      "confidence": 0.90
    }}
  ]
}}

全局约束：
- 金额字段使用数字，不使用字符串
- 【严禁遗漏商品】必须列出凭证上每一个商品行；无法分类时将 main_category 设为"其他"
- 必须输出有效 JSON，不得有多余注释或 trailing comma
</output_schema>

<field_rules>

<rule id="merchant">
商店名(merchant)：
{merchant_instruction}
</rule>

<rule id="purchased_at">
日期(purchased_at)：
- 仔细查找凭证上的购买日期、交易日期、下单时间、付款时间或打印日期
- 找到则转为 ISO 8601 格式（如 2024-03-15T14:30:00）
- 凭证上确实没有任何日期信息，填 null
</rule>

<rule id="categories">
主类(main_category)：
{categories_instruction}
</rule>

<rule id="unit">
单位(unit)：
- 只能从以下枚举中选择：个, 包, 袋, 盒, 瓶, 罐, 桶, 杯, 根, 条, 块, 片, 只, 把, 份, 串, 组, 打, 支, 卷, 升, 毫升, 千克, 克, 斤, 磅, 盘, 碗
- 规格/净含量（如 130g、500ml）放入 tags，不放 unit
- 无法判断时默认填"个"
- 禁止使用英文单位（pack/bottle/kg 等）
</rule>

<rule id="brand">
品牌(brand)：
- 只有收据上能明确看到品牌名时才填写（如"李锦记"、"Hellmann's"）
- 收据未标注品牌，填 null；不猜测，不用商品编码充当品牌
- 英文品牌名保留英文原文（不翻译品牌名）
</rule>

<rule id="item_name">
商品名(name)：
- 收据同时有中英文名时，以中文名为准识别商品和分类
- 英文收据上的商品名翻译为中文通用名称
- 【关键】必须把商品名作为整体理解，严禁拆字归类：
  × 错误："咸蛋黄油条" → 只看"咸" → 归为调味品
  √ 正确："咸蛋黄油条" → 整体是咸蛋黄味油条 → 零食糕点
  × 错误："红油豆瓣酱" → 只看"油" → 归为食用油
  √ 正确："红油豆瓣酱" → 整体是豆瓣酱 → 调味品
- 先理解完整商品名的含义，再决定 main_category
</rule>

<rule id="language">
语言规范：
- main_category、name、unit 字段统一使用中文
- merchant 和 address 保留收据原文，不翻译
- brand 保留原文（中英文均可）
- tags 中的规格信息保留原始标注（如 "130g"、"310ml"）
</rule>

<rule id="price_reading">
价格解读（unit_price / quantity / discount）：
- 只需识别三个字段：unit_price（折扣前单价）、quantity（数量）、discount（该商品折扣金额）
- 系统会自动按公式计算总价：total_price = unit_price × quantity - discount，不要输出 total_price
- 【关键】收据/小票上商品行右侧显示的金额通常是该商品的**行总价**（而非单价）：
  × 错误："JS GARLIC x 4  £0.87" → quantity=4, unit_price=0.87（会算出 3.48）
  √ 正确："JS GARLIC x 4  £0.87" → quantity=4, unit_price=0.22（0.87÷4，折后总价仍为 0.87）
  - 即：若右侧金额是行总价，则 unit_price = 行总价 ÷ quantity
- 若收据上明确标注了单价（如 "2 @ £1.50"），直接使用 1.50 作为 unit_price
- 折扣处理：
  - 若商品行有划线原价与折后价（如原价 £2.00 折后 £1.50），则 unit_price=2.00, discount=(2.00-1.50)*quantity
  - 若商品行下方有"会员价/满减/优惠 -£0.50"等单独的减项，则 discount=0.50 填入该商品
  - 商品行未标注任何折扣时，discount 填 0
- 所有金额保留两位小数
</rule>

</field_rules>

<online_order>
网购订单截图的特殊处理：
- merchant：使用店铺名称（非平台名）。如"盒马鲜生"而非"淘宝"；若只能看到平台名则用平台名
- purchased_at：优先使用"下单时间/付款时间"，其次"发货时间/完成时间"
- total：使用"实付款/实际支付"金额；如有运费则包含在 total 中，不单独列为商品
- discount：优先级别折扣/满减/优惠券等总折扣金额，从原价与实付差额推算
- items：每个商品行独立提取，规格（如颜色/尺码/型号）放入 tags
- unit_price/total_price：使用实际支付价格，非划线原价
- 若截图包含多个独立订单，合并为一份 JSON，merchant 取主要/首个店铺名
- 网购订单中常见的"运费险"、"服务费"等非商品项，忽略不提取
</online_order>

<multi_image>
若收到多张图片，它们属于同一笔购物（正反面、分段拍摄或长截图分割）：
- 综合所有图片信息，输出一份完整 JSON
- 去重判断：名称和价格均相同的商品行只保留一次；若同一商品确实出现多次（quantity≥2 或独立的两行），则分别保留
- 以有价格信息的图片为准
</multi_image>
""".strip()

_MERCHANTS_WITH_EXISTING = (
    "- 系统中已有以下商店：【{existing}】\n"
    "- 如果收据上的商店名与上述某个商店是同一家（仅大小写、空格、分店后缀等差异），请使用已有名称\n"
    "- 如果是全新的商店，保留收据原文"
)

_MERCHANTS_NO_EXISTING = (
    "- 保留凭证上的商店/店铺原文，不翻译"
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
    choices = data.get("choices")
    if not choices:
        error_msg = data.get("error", {}).get("message", "") if isinstance(data.get("error"), dict) else str(data.get("error", ""))
        raise RuntimeError(f"API 返回空结果 (choices 为空): {error_msg or data}")
    message = choices[0].get("message", {})
    content = message.get("content") or ""
    if not content:
        raise RuntimeError(f"API 未返回有效内容: {message}")
    content = _strip_json_fences(content)
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

        choices = chunk.get("choices") or [{}]
        delta = choices[0].get("delta", {})

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
