import time
import logging

logger = logging.getLogger(__name__)

# Module-level in-memory cache: {"rate": float, "updated_at": float}
_cache: dict | None = None
_CACHE_TTL = 3600  # 1 hour


def get_gbp_cny_rate() -> dict:
    """Fetch GBP→CNY exchange rate with 1-hour cache.

    Returns dict with keys: rate, source, target, cached, stale, updated_at
    """
    global _cache
    now = time.time()

    # Return fresh cache
    if _cache and (now - _cache["updated_at"]) < _CACHE_TTL:
        return {
            "rate": _cache["rate"],
            "source": "GBP",
            "target": "CNY",
            "cached": True,
            "stale": False,
            "updated_at": _cache["updated_at"],
        }

    # Try fetching from yfinance
    try:
        import yfinance as yf

        ticker = yf.Ticker("GBPCNY=X")
        hist = ticker.history(period="1d")
        if hist.empty:
            raise ValueError("No data returned from yfinance")
        rate = float(hist["Close"].iloc[-1])
        _cache = {"rate": rate, "updated_at": now}
        return {
            "rate": rate,
            "source": "GBP",
            "target": "CNY",
            "cached": False,
            "stale": False,
            "updated_at": now,
        }
    except Exception as exc:
        logger.warning("Failed to fetch exchange rate: %s", exc)
        # Return stale cache if available
        if _cache:
            return {
                "rate": _cache["rate"],
                "source": "GBP",
                "target": "CNY",
                "cached": True,
                "stale": True,
                "updated_at": _cache["updated_at"],
            }
        return {"error": str(exc)}
