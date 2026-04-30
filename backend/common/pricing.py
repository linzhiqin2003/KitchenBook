"""模型计费表、模型归一化与开销估算。

价格按"每百万 token 多少 RMB"配置。cache_tokens 按 cache 价计，
prompt_tokens 中扣掉 cache_tokens 后的部分按 input 价计。
不区分 cache 读写（按用户约定，read+write 合并到 cache_tokens 一并按 cache 价）。

新增模型：直接在 PRICING 字典加一条；未列出的模型回退到 DEFAULT_MODEL。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional


# RMB per 1 million tokens
PRICING: Dict[str, Dict[str, Decimal]] = {
    "deepseek-v4-flash": {
        "input": Decimal("1"),
        "output": Decimal("2"),
        "cache": Decimal("0.02"),
    },
    "deepseek-v4-pro": {
        "input": Decimal("2"),
        "output": Decimal("6"),
        "cache": Decimal("0.25"),
    },
    "xiaomi/mimo-v2.5": {
        "input": Decimal("0.4"),
        "output": Decimal("2"),
        "cache": Decimal("0.08"),
    },
    "xiaomi/mimo-v2.5-pro": {
        "input": Decimal("1"),
        "output": Decimal("3"),
        "cache": Decimal("0.2"),
    },
}

DEFAULT_MODEL = "deepseek-v4-flash"
CURRENCY = "CNY"
MODEL_ALIASES: Dict[str, str] = {
    "Hermes": DEFAULT_MODEL,
    "hermes-agent": DEFAULT_MODEL,
}


def normalize_model_name(model: Optional[str]) -> str:
    """把历史路由名/空值归一化成统计用的模型名。"""
    if not model:
        return DEFAULT_MODEL
    return MODEL_ALIASES.get(model, model)


def get_pricing(model: Optional[str]) -> Dict[str, Decimal]:
    """返回指定模型的价格表，未知模型回退到默认模型。"""
    normalized = normalize_model_name(model)
    if normalized in PRICING:
        return PRICING[normalized]
    return PRICING[DEFAULT_MODEL]


def estimate_cost(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    cache_tokens: int = 0,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """计算单次/累计调用的费用。

    `prompt_tokens` 应为 OpenAI 语义的总 prompt（含 cache hit）。
    `cache_tokens` 是其中走 cache 价的部分。
    `non_cache_input = prompt_tokens - cache_tokens` 走 input 价。

    返回：
      {
        "model": "deepseek-v4-flash",
        "currency": "CNY",
        "input_cost": "1.234567",   # 字符串以保留精度
        "cache_cost": "0.001234",
        "output_cost": "2.345678",
        "total_cost": "3.581479",
        "non_cache_input_tokens": 12345,
      }
    """
    prompt_tokens = max(int(prompt_tokens or 0), 0)
    completion_tokens = max(int(completion_tokens or 0), 0)
    cache_tokens = max(int(cache_tokens or 0), 0)
    cache_tokens = min(cache_tokens, prompt_tokens)  # 防御：cache 不会超过 prompt
    non_cache_input = prompt_tokens - cache_tokens

    normalized_model = normalize_model_name(model)
    pricing = get_pricing(normalized_model)
    million = Decimal("1000000")
    input_cost = (Decimal(non_cache_input) / million) * pricing["input"]
    cache_cost = (Decimal(cache_tokens) / million) * pricing["cache"]
    output_cost = (Decimal(completion_tokens) / million) * pricing["output"]
    total_cost = input_cost + cache_cost + output_cost

    # 量化到 6 位小数（够看清几分钱）
    q = Decimal("0.000001")
    return {
        "model": normalized_model if normalized_model in PRICING else DEFAULT_MODEL,
        "currency": CURRENCY,
        "input_cost": str(input_cost.quantize(q)),
        "cache_cost": str(cache_cost.quantize(q)),
        "output_cost": str(output_cost.quantize(q)),
        "total_cost": str(total_cost.quantize(q)),
        "non_cache_input_tokens": non_cache_input,
    }
