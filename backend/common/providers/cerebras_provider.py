"""
Cerebras Provider Implementation

Supports fast inference LLM with rate-limit-aware model rotation.
Primary model: gpt-oss-120b, fallback: zai-glm-4.7.
"""

import time
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from cerebras.cloud.sdk import Cerebras, AsyncCerebras

from .base import (
    ProviderConfig,
    ProviderType,
    ServiceType,
    Message,
    LLMResponse,
    LLMProvider,
)

logger = logging.getLogger(__name__)


# Rate limits per model (from Cerebras free tier)
MODEL_RATE_LIMITS = {
    "gpt-oss-120b": {
        "rpm": 30, "rph": 900, "rpd": 14400,
        "tpm": 60000, "tph": 1000000, "tpd": 1000000,
    },
    "zai-glm-4.7": {
        "rpm": 10, "rph": 100, "rpd": 100,
        "tpm": 60000, "tph": 1000000, "tpd": 1000000,
    },
}

# Default model rotation order
DEFAULT_MODEL_CHAIN = ["gpt-oss-120b", "zai-glm-4.7"]

# Cooldown after hitting rate limit before retrying the model (seconds)
RATE_LIMIT_COOLDOWN = 65  # slightly over 1 minute for RPM reset

# Reasoning models need higher max_tokens because reasoning consumes tokens
# before generating the final content. min_max_tokens ensures enough headroom.
REASONING_MODELS = {
    "zai-glm-4.7": {"min_max_tokens": 1024},
}


class ModelRotator:
    """
    Tracks rate limit hits per model and selects the best available model.

    When a model returns 429, records the timestamp. On the next request,
    picks the first model in the chain whose cooldown has expired.
    """

    def __init__(self, model_chain: List[str], cooldown: float = RATE_LIMIT_COOLDOWN):
        self.model_chain = model_chain
        self.cooldown = cooldown
        # model -> timestamp of last 429 hit
        self._rate_limited_at: Dict[str, float] = {}

    def mark_rate_limited(self, model: str):
        self._rate_limited_at[model] = time.time()
        logger.warning(f"Model {model} hit rate limit, cooldown {self.cooldown}s")

    def is_available(self, model: str) -> bool:
        hit_time = self._rate_limited_at.get(model)
        if hit_time is None:
            return True
        return (time.time() - hit_time) >= self.cooldown

    def pick_model(self) -> str:
        for model in self.model_chain:
            if self.is_available(model):
                return model
        # All models rate-limited, return primary and let it fail naturally
        logger.warning("All models rate-limited, falling back to primary")
        return self.model_chain[0]

    @property
    def status(self) -> Dict[str, Any]:
        now = time.time()
        return {
            model: {
                "available": self.is_available(model),
                "cooldown_remaining": max(
                    0, self.cooldown - (now - self._rate_limited_at.get(model, 0))
                ) if model in self._rate_limited_at else 0,
            }
            for model in self.model_chain
        }


class CerebrasLLMProvider(LLMProvider):
    """
    Cerebras LLM Provider with automatic model rotation on rate limit.

    Uses gpt-oss-120b as primary, falls back to zai-glm-4.7 on 429.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        self.client = Cerebras(api_key=config.api_key)
        self.async_client = AsyncCerebras(api_key=config.api_key)

        model_chain = config.extra_params.get("model_chain", DEFAULT_MODEL_CHAIN)
        cooldown = config.extra_params.get("cooldown", RATE_LIMIT_COOLDOWN)
        self.rotator = ModelRotator(model_chain, cooldown)
        self.default_model = config.model or model_chain[0]

    def get_supported_services(self) -> List[ServiceType]:
        return [ServiceType.LLM]

    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _resolve_model(self, model: Optional[str]) -> str:
        if model and model not in [m for m in self.rotator.model_chain]:
            return model
        return self.rotator.pick_model()

    def _ensure_max_tokens(self, model: str, max_tokens: Optional[int]) -> Optional[int]:
        """Reasoning models need higher max_tokens to leave room for thinking."""
        cfg = REASONING_MODELS.get(model)
        if cfg is None:
            return max_tokens
        min_val = cfg["min_max_tokens"]
        if max_tokens is None or max_tokens < min_val:
            return min_val
        return max_tokens

    @staticmethod
    def _extract_content(message) -> str:
        """Extract content from response, falling back to reasoning for thinking models."""
        if message.content:
            return message.content
        reasoning = getattr(message, "reasoning", None)
        if reasoning:
            return reasoning
        return ""

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        # Cerebras SDK raises APIStatusError with status_code 429
        status = getattr(exc, "status_code", None)
        if status == 429:
            return True
        # Fallback: check message
        msg = str(exc).lower()
        return "rate limit" in msg or "429" in msg

    def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        used_model = self._resolve_model(model)
        effective_max_tokens = self._ensure_max_tokens(used_model, max_tokens)
        try:
            completion = self.client.chat.completions.create(
                model=used_model,
                messages=self._convert_messages(messages),
                temperature=temperature,
                max_tokens=effective_max_tokens,
                **kwargs,
            )
            choice = completion.choices[0]
            return LLMResponse(
                content=self._extract_content(choice.message),
                role=choice.message.role,
                finish_reason=choice.finish_reason,
                usage=dict(completion.usage) if completion.usage else None,
                raw_response=completion,
            )
        except Exception as e:
            if self._is_rate_limit_error(e):
                self.rotator.mark_rate_limited(used_model)
                fallback = self._resolve_model(model)
                if fallback != used_model:
                    logger.info(f"Retrying with fallback model: {fallback}")
                    return self.chat(messages, fallback, temperature, max_tokens, **kwargs)
            logger.error(f"Cerebras chat error ({used_model}): {e}")
            raise

    async def chat_async(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        used_model = self._resolve_model(model)
        effective_max_tokens = self._ensure_max_tokens(used_model, max_tokens)
        try:
            completion = await self.async_client.chat.completions.create(
                model=used_model,
                messages=self._convert_messages(messages),
                temperature=temperature,
                max_tokens=effective_max_tokens,
                **kwargs,
            )
            choice = completion.choices[0]
            return LLMResponse(
                content=self._extract_content(choice.message),
                role=choice.message.role,
                finish_reason=choice.finish_reason,
                usage=dict(completion.usage) if completion.usage else None,
                raw_response=completion,
            )
        except Exception as e:
            if self._is_rate_limit_error(e):
                self.rotator.mark_rate_limited(used_model)
                fallback = self._resolve_model(model)
                if fallback != used_model:
                    logger.info(f"Retrying with fallback model: {fallback}")
                    return await self.chat_async(messages, fallback, temperature, max_tokens, **kwargs)
            logger.error(f"Cerebras async chat error ({used_model}): {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        used_model = self._resolve_model(model)
        effective_max_tokens = self._ensure_max_tokens(used_model, max_tokens)
        try:
            stream = self.client.chat.completions.create(
                model=used_model,
                messages=self._convert_messages(messages),
                temperature=temperature,
                max_tokens=effective_max_tokens,
                stream=True,
                **kwargs,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            if self._is_rate_limit_error(e):
                self.rotator.mark_rate_limited(used_model)
                fallback = self._resolve_model(model)
                if fallback != used_model:
                    logger.info(f"Stream retrying with fallback model: {fallback}")
                    async for chunk_text in self.chat_stream(
                        messages, fallback, temperature, max_tokens, **kwargs
                    ):
                        yield chunk_text
                    return
            logger.error(f"Cerebras stream error ({used_model}): {e}")
            raise
