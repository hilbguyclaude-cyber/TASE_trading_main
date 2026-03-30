"""
Yahoo Finance client for TASE trading system.

Provides price fetching with in-memory caching (60-second TTL) to reduce API calls.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
import yfinance as yf

# In-memory cache: {ticker: {'price': float, 'timestamp': datetime}}
_price_cache: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 60


class PriceFetchError(Exception):
    """Raised when price cannot be fetched from yfinance"""
    pass


def get_current_price(ticker: str, use_cache: bool = True) -> float:
    """
    Fetch current stock price with optional caching.

    Args:
        ticker: Stock ticker symbol (e.g., 'TSEM.TA' for Tower Semiconductor)
        use_cache: If True, return cached price if available and fresh (< 60 seconds old)

    Returns:
        float: Current stock price

    Raises:
        PriceFetchError: If price cannot be fetched
    """
    # Check cache if enabled
    if use_cache:
        cached = get_cached_price(ticker)
        if cached:
            age = (datetime.now() - cached['timestamp']).total_seconds()
            if age < CACHE_TTL_SECONDS:
                return cached['price']

    # Fetch fresh price
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Try multiple price fields (different tickers use different keys)
        price = info.get('currentPrice') or info.get('regularMarketPrice')

        if price is None or price <= 0:
            raise PriceFetchError(f"No valid price found for {ticker}")

        # Update cache
        _price_cache[ticker] = {
            'price': float(price),
            'timestamp': datetime.now()
        }

        return float(price)

    except Exception as e:
        raise PriceFetchError(f"Failed to fetch price for {ticker}: {e}")


def get_cached_price(ticker: str) -> Optional[Dict]:
    """
    Get cached price for a ticker (any age).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with 'price' and 'timestamp' keys if cached, None otherwise
    """
    return _price_cache.get(ticker)


def clear_cache(ticker: Optional[str] = None) -> None:
    """
    Clear price cache.

    Args:
        ticker: Specific ticker to clear, or None to clear all
    """
    if ticker:
        _price_cache.pop(ticker, None)
    else:
        _price_cache.clear()


def get_price_with_fallback(
    ticker: str,
    fallback_price: Optional[float] = None
) -> float:
    """
    Fetch price with fallback to stale cached data or provided fallback.

    Args:
        ticker: Stock ticker symbol
        fallback_price: Fallback price if fetch fails and no cache available

    Returns:
        float: Current price, cached price, or fallback price

    Raises:
        PriceFetchError: If all fetch methods fail and no fallback available
    """
    try:
        return get_current_price(ticker, use_cache=True)
    except PriceFetchError:
        # Try stale cache
        cached = get_cached_price(ticker)
        if cached:
            return cached['price']

        # Try provided fallback
        if fallback_price is not None:
            return fallback_price

        raise PriceFetchError(f"All price fetch methods failed for {ticker}")
