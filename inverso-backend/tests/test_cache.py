"""
Tests para el sistema de caché TTL de market_data.
"""
import time
from unittest.mock import patch
from services.market_data import _cache, _cache_get, _cache_set


def setup_function():
    _cache.clear()


def test_cache_miss_returns_none():
    assert _cache_get("nonexistent") is None


def test_cache_set_and_get():
    _cache_set("test_key", {"value": 42}, ttl=60)
    assert _cache_get("test_key") == {"value": 42}


def test_cache_expired_returns_none():
    _cache_set("expired_key", {"value": 1}, ttl=0)
    time.sleep(0.01)
    assert _cache_get("expired_key") is None


def test_cache_hit_avoids_yfinance_call():
    """Si hay caché válido, yfinance no se llama."""
    import asyncio
    from services.market_data import get_asset_data
    _cache_set("asset:GGAL", {"ticker": "GGAL", "price": 9999.0}, ttl=60)

    with patch("services.market_data.yf.Ticker") as mock_yf:
        result = asyncio.run(get_asset_data("GGAL"))

    mock_yf.assert_not_called()
    assert result["price"] == 9999.0
