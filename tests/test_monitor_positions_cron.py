import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.cron.monitor_positions import monitor_positions


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies"""
    with patch('api.cron.monitor_positions.get_open_positions') as mock_get_pos, \
         patch('api.cron.monitor_positions.get_price_with_fallback') as mock_price, \
         patch('api.cron.monitor_positions.update_peak_price') as mock_update_peak, \
         patch('api.cron.monitor_positions.should_sell') as mock_should_sell, \
         patch('api.cron.monitor_positions.close_position') as mock_close, \
         patch('api.cron.monitor_positions.get_israel_time') as mock_time, \
         patch('api.cron.monitor_positions.log_system_event') as mock_log:

        israel_tz = pytz.timezone('Asia/Jerusalem')
        mock_time.return_value = israel_tz.localize(datetime(2024, 3, 31, 11, 0))

        yield {
            'get_positions': mock_get_pos,
            'price': mock_price,
            'update_peak': mock_update_peak,
            'should_sell': mock_should_sell,
            'close': mock_close,
            'time': mock_time,
            'log': mock_log
        }


def test_monitor_positions_no_open_positions(mock_dependencies):
    """Test with no open positions"""
    mock_dependencies['get_positions'].return_value = []

    result = monitor_positions()

    assert result['success'] is True
    assert result['message'] == 'No open positions'
    assert result['positions_checked'] == 0
    assert result['positions_closed'] == 0


def test_monitor_positions_fetch_error(mock_dependencies):
    """Test handling of position fetch errors"""
    mock_dependencies['get_positions'].side_effect = Exception("Database connection failed")

    result = monitor_positions()

    assert result['success'] is False
    assert 'Failed to fetch positions' in result['message']


def test_monitor_positions_hold_position(mock_dependencies):
    """Test monitoring position that should be held"""
    # Mock open position
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 30))

    positions = [{
        'id': 'pos-123',
        'ticker': 'TSEM.TA',
        'entry_price': 100.0,
        'peak_price': 102.0,
        'entry_time': entry_time.isoformat()
    }]

    mock_dependencies['get_positions'].return_value = positions
    mock_dependencies['price'].return_value = 101.5  # Between entry and peak
    mock_dependencies['should_sell'].return_value = (False, "Hold position")

    result = monitor_positions()

    assert result['success'] is True
    assert result['positions_checked'] == 1
    assert result['positions_closed'] == 0
    mock_dependencies['close'].assert_not_called()


def test_monitor_positions_update_peak(mock_dependencies):
    """Test peak price update when current price exceeds peak"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 30))

    positions = [{
        'id': 'pos-123',
        'ticker': 'TSEM.TA',
        'entry_price': 100.0,
        'peak_price': 102.0,
        'entry_time': entry_time.isoformat()
    }]

    mock_dependencies['get_positions'].return_value = positions
    mock_dependencies['price'].return_value = 105.0  # New peak!
    mock_dependencies['should_sell'].return_value = (False, "Hold position")

    result = monitor_positions()

    assert result['success'] is True
    assert result['peak_updates'] == 1
    mock_dependencies['update_peak'].assert_called_once_with('pos-123', 105.0)


def test_monitor_positions_close_on_time(mock_dependencies):
    """Test closing position after 60 minutes"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))

    positions = [{
        'id': 'pos-123',
        'ticker': 'TSEM.TA',
        'entry_price': 100.0,
        'peak_price': 105.0,
        'entry_time': entry_time.isoformat()
    }]

    mock_dependencies['get_positions'].return_value = positions
    mock_dependencies['price'].return_value = 103.0
    mock_dependencies['should_sell'].return_value = (True, "Time limit reached (60min), profit: +3.00%")

    # Mock close_position response
    mock_dependencies['close'].return_value = {
        'id': 'pos-123',
        'exit_price': 103.0,
        'profit_loss_ils': 150.0,
        'profit_loss_percent': 3.0
    }

    result = monitor_positions()

    assert result['success'] is True
    assert result['positions_closed'] == 1
    mock_dependencies['close'].assert_called_once()


def test_monitor_positions_close_on_stop_loss(mock_dependencies):
    """Test closing position on stop loss trigger"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 30))

    positions = [{
        'id': 'pos-123',
        'ticker': 'TSEM.TA',
        'entry_price': 100.0,
        'peak_price': 110.0,
        'entry_time': entry_time.isoformat()
    }]

    mock_dependencies['get_positions'].return_value = positions
    mock_dependencies['price'].return_value = 107.0  # -2.73% from peak
    mock_dependencies['should_sell'].return_value = (True, "Stop loss triggered: -2.73% drop from peak")

    # Mock close_position response
    mock_dependencies['close'].return_value = {
        'id': 'pos-123',
        'exit_price': 107.0,
        'profit_loss_ils': 350.0,
        'profit_loss_percent': 7.0
    }

    result = monitor_positions()

    assert result['success'] is True
    assert result['positions_closed'] == 1
    mock_dependencies['close'].assert_called_with('pos-123', 107.0, "Stop loss triggered: -2.73% drop from peak")


def test_monitor_positions_multiple_positions(mock_dependencies):
    """Test monitoring multiple positions"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))

    positions = [
        {'id': 'pos-1', 'ticker': 'TSEM.TA', 'entry_price': 100.0, 'peak_price': 102.0, 'entry_time': entry_time.isoformat()},
        {'id': 'pos-2', 'ticker': 'TEVA.TA', 'entry_price': 50.0, 'peak_price': 52.0, 'entry_time': entry_time.isoformat()},
        {'id': 'pos-3', 'ticker': 'ICL.TA', 'entry_price': 75.0, 'peak_price': 78.0, 'entry_time': entry_time.isoformat()}
    ]

    mock_dependencies['get_positions'].return_value = positions

    # Mock prices
    mock_dependencies['price'].side_effect = [101.5, 51.0, 76.5]

    # Mock sell decisions - close first two, hold third
    mock_dependencies['should_sell'].side_effect = [
        (True, "Time limit reached"),
        (True, "Stop loss"),
        (False, "Hold")
    ]

    # Mock close responses
    mock_dependencies['close'].side_effect = [
        {'id': 'pos-1', 'exit_price': 101.5, 'profit_loss_ils': 75.0, 'profit_loss_percent': 1.5},
        {'id': 'pos-2', 'exit_price': 51.0, 'profit_loss_ils': 50.0, 'profit_loss_percent': 2.0}
    ]

    result = monitor_positions()

    assert result['success'] is True
    assert result['positions_checked'] == 3
    assert result['positions_closed'] == 2
    assert mock_dependencies['close'].call_count == 2


def test_monitor_positions_price_fetch_fallback(mock_dependencies):
    """Test fallback to entry price when price fetch fails"""
    from lib.yfinance_client import PriceFetchError

    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 30))

    positions = [{
        'id': 'pos-123',
        'ticker': 'TSEM.TA',
        'entry_price': 100.0,
        'peak_price': 102.0,
        'entry_time': entry_time.isoformat()
    }]

    mock_dependencies['get_positions'].return_value = positions
    mock_dependencies['price'].side_effect = PriceFetchError("API error")
    mock_dependencies['should_sell'].return_value = (False, "Hold")

    result = monitor_positions()

    assert result['success'] is True
    assert result['positions_checked'] == 1
    # Should continue despite price fetch error


def test_monitor_positions_error_handling(mock_dependencies):
    """Test that one failing position doesn't stop others"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 30))

    positions = [
        {'id': 'pos-1', 'ticker': 'TSEM.TA', 'entry_price': 100.0, 'peak_price': 102.0, 'entry_time': entry_time.isoformat()},
        {'id': 'pos-2', 'ticker': 'TEVA.TA', 'entry_price': 50.0, 'peak_price': 52.0, 'entry_time': entry_time.isoformat()}
    ]

    mock_dependencies['get_positions'].return_value = positions

    # First position fails, second succeeds
    mock_dependencies['price'].side_effect = [Exception("Unexpected error"), 51.0]
    mock_dependencies['should_sell'].return_value = (False, "Hold")

    result = monitor_positions()

    assert result['success'] is True
    assert result['positions_checked'] == 1  # Only second position completed
    assert len(result['errors']) == 1
