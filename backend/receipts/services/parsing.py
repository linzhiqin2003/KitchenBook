import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from pydantic import BaseModel, Field, ValidationError


class ParsedItem(BaseModel):
    main_category: str | None = ""
    sub_category: str | None = ""
    name: str
    brand: str | None = ""
    quantity: float | None = 1
    unit: str | None = ""
    unit_price: float | None = None
    total_price: float | None = None
    tags: list[str] = Field(default_factory=list)
    confidence: float | None = None


class ParsedReceipt(BaseModel):
    merchant: str | None = ""
    address: str | None = ""
    purchased_at: str | None = None
    currency: str | None = "GBP"
    subtotal: float | None = None
    tax: float | None = None
    discount: float | None = None
    total: float | None = None
    items: list[ParsedItem] = Field(default_factory=list)


@dataclass
class ParseResult:
    receipt: ParsedReceipt
    raw_json: dict[str, Any]


def _strip_code_fence(text: str) -> str:
    if "```" not in text:
        return text
    parts = text.split("```")
    if len(parts) >= 3:
        return parts[1].strip()
    return text


def extract_json(text: str) -> dict[str, Any]:
    text = _strip_code_fence(text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class NotReceiptError(Exception):
    """Raised when the image is not a receipt."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def parse_receipt_payload(text: str) -> ParseResult:
    raw = extract_json(text)
    if not raw.get("is_receipt", True):
        reason = raw.get("reason", "图片中未检测到收据/发票")
        raise NotReceiptError(reason)
    try:
        receipt = ParsedReceipt.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"LLM output schema invalid: {exc}") from exc
    return ParseResult(receipt=receipt, raw_json=raw)


def parse_datetime_with_tz(value: str | None):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_default_timezone())
    return dt


def to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
