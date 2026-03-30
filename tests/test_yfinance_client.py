import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from lib.yfinance_client import (
    get_current_price,
    get_cached_price,
    clear_cache,
    get_price_with_fallback,
    PriceFetchError,
    _price_cache,
    CACHE_TTL_SECONDS
)


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Clear cache before each test"""
    clear_cache()
    yield
    clear_cache()


def test_get_current_price_success():
    """Test successful price fetch"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_info = {'currentPrice': 42.50}
        mock_ticker.return_value.info = mock_info

        price = get_current_price('TSEM.TA', use_cache=False)

        assert price == 42.50
        assert isinstance(price, float)


def test_get_current_price_regular_market_price():
    """Test price fetch using regularMarketPrice field"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_info = {'regularMarketPrice': 100.75}
        mock_ticker.return_value.info = mock_info

        price = get_current_price('TEVA.TA', use_cache=False)

        assert price == 100.75


def test_get_current_price_caching():
    """Test that price is cached after first fetch"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_info = {'currentPrice': 50.0}
        mock_ticker.return_value.info = mock_info

        # First call - should fetch
        price1 = get_current_price('TEST.TA', use_cache=True)
        assert price1 == 50.0
        assert mock_ticker.call_count == 1

        # Second call - should use cache
        price2 = get_current_price('TEST.TA', use_cache=True)
        assert price2 == 50.0
        assert mock_ticker.call_count == 1  # No additional API call


def test_get_current_price_cache_expiry():
    """Test that expired cache is refreshed"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_info = {'currentPrice': 60.0}
        mock_ticker.return_value.info = mock_info

        # First fetch
        price1 = get_current_price('EXPIRE.TA', use_cache=True)
        assert price1 == 60.0

        # Manually expire cache by setting old timestamp
        _price_cache['EXPIRE.TA']['timestamp'] = datetime.now() - timedelta(seconds=CACHE_TTL_SECONDS + 1)

        # Update mock to return different price
        mock_info['currentPrice'] = 65.0

        # Second fetch - should refresh due to expiry
        price2 = get_current_price('EXPIRE.TA', use_cache=True)
        assert price2 == 65.0
        assert mock_ticker.call_count == 2


def test_get_current_price_no_cache():
    """Test that use_cache=False bypasses cache"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_info = {'currentPrice': 70.0}
        mock_ticker.return_value.info = mock_info

        # First call with cache
        get_current_price('NOCACHE.TA', use_cache=True)

        # Update mock
        mock_info['currentPrice'] = 75.0

        # Second call without cache - should fetch fresh
        price = get_current_price('NOCACHE.TA', use_cache=False)
        assert price == 75.0
        assert mock_ticker.call_count == 2


def test_get_current_price_fetch_error():
    """Test handling of fetch failures"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.info = {}  # No price fields

        with pytest.raises(PriceFetchError, match="No valid price found"):
            get_current_price('FAIL.TA', use_cache=False)


def test_get_current_price_invalid_price():
    """Test handling of invalid prices"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.info = {'currentPrice': 0}  # Invalid

        with pytest.raises(PriceFetchError, match="No valid price found"):
            get_current_price('ZERO.TA', use_cache=False)


def test_get_current_price_exception():
    """Test handling of API exceptions"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_ticker.side_effect = Exception("API Error")

        with pytest.raises(PriceFetchError, match="Failed to fetch price"):
            get_current_price('ERROR.TA', use_cache=False)


def test_get_cached_price():
    """Test retrieving cached price"""
    # Cache a price manually
    _price_cache['CACHED.TA'] = {
        'price': 123.45,
        'timestamp': datetime.now()
    }

    cached = get_cached_price('CACHED.TA')

    assert cached is not None
    assert cached['price'] == 123.45
    assert isinstance(cached['timestamp'], datetime)


def test_get_cached_price_not_found():
    """Test retrieving non-existent cache"""
    cached = get_cached_price('NOTFOUND.TA')
    assert cached is None


def test_clear_cache_specific():
    """Test clearing specific ticker cache"""
    _price_cache['TICKER1.TA'] = {'price': 10.0, 'timestamp': datetime.now()}
    _price_cache['TICKER2.TA'] = {'price': 20.0, 'timestamp': datetime.now()}

    clear_cache('TICKER1.TA')

    assert 'TICKER1.TA' not in _price_cache
    assert 'TICKER2.TA' in _price_cache


def test_clear_cache_all():
    """Test clearing all cache"""
    _price_cache['TICKER1.TA'] = {'price': 10.0, 'timestamp': datetime.now()}
    _price_cache['TICKER2.TA'] = {'price': 20.0, 'timestamp': datetime.now()}

    clear_cache()

    assert len(_price_cache) == 0


def test_get_price_with_fallback_success():
    """Test fallback function with successful fetch"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_info = {'currentPrice': 88.0}
        mock_ticker.return_value.info = mock_info

        price = get_price_with_fallback('SUCCESS.TA', fallback_price=99.0)

        assert price == 88.0


def test_get_price_with_fallback_uses_stale_cache():
    """Test fallback to stale cached data"""
    # Cache an old price
    _price_cache['STALE.TA'] = {
        'price': 111.0,
        'timestamp': datetime.now() - timedelta(seconds=CACHE_TTL_SECONDS + 100)
    }

    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.info = {}  # Fetch will fail

        price = get_price_with_fallback('STALE.TA', fallback_price=222.0)

        assert price == 111.0  # Should use stale cache, not fallback


def test_get_price_with_fallback_uses_fallback():
    """Test fallback to provided fallback price"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.info = {}  # Fetch will fail

        price = get_price_with_fallback('FALLBACK.TA', fallback_price=333.0)

        assert price == 333.0


def test_get_price_with_fallback_no_fallback():
    """Test failure when no fallback available"""
    with patch('lib.yfinance_client.yf.Ticker') as mock_ticker:
        mock_ticker.return_value.info = {}  # Fetch will fail

        with pytest.raises(PriceFetchError, match="All price fetch methods failed"):
            get_price_with_fallback('NOFALLBACK.TA')
