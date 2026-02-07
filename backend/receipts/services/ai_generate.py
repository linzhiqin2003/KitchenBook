import os

from cerebras.cloud.sdk import Cerebras

from .doubao import _build_prompt

# JSON Schema matching ParsedReceipt structure
RECEIPT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_receipt": {"type": "boolean"},
        "merchant": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]},
        "purchased_at": {"type": ["string", "null"]},
        "currency": {"type": "string"},
        "subtotal": {"type": ["number", "null"]},
        "tax": {"type": ["number", "null"]},
        "discount": {"type": ["number", "null"]},
        "total": {"type": ["number", "null"]},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "main_category": {"type": ["string", "null"]},
                    "sub_category": {"type": ["string", "null"]},
                    "name": {"type": "string"},
                    "brand": {"type": ["string", "null"]},
                    "quantity": {"type": ["number", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "unit_price": {"type": ["number", "null"]},
                    "total_price": {"type": ["number", "null"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": ["number", "null"]},
                },
                "required": ["name", "total_price", "tags"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["is_receipt", "merchant", "currency", "total", "items"],
    "additionalProperties": False,
}


def generate_receipt_from_description(description: str) -> str:
    """Generate a receipt JSON from a text description using Cerebras LLM.

    Returns a JSON string in the same format as image-based receipt parsing.
    """
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing CEREBRAS_API_KEY")

    client = Cerebras(api_key=api_key)
    system_prompt = _build_prompt()

    completion = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "请根据以下文字描述生成账单 JSON（与收据解析输出格式完全一致）。\n"
                    "注意：is_receipt 设为 true，confidence 设为 0.95。\n"
                    "如果描述中没有提到日期，purchased_at 设为 null。\n"
                    "如果描述中没有提到总价但有各商品价格，请自动计算 subtotal 和 total。\n\n"
                    f"描述：{description}"
                ),
            },
        ],
        temperature=0.3,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "receipt_schema",
                "strict": True,
                "schema": RECEIPT_JSON_SCHEMA,
            },
        },
    )
    return completion.choices[0].message.content
