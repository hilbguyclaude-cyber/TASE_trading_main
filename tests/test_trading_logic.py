import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch
from lib.trading_logic import (
    should_buy,
    should_sell,
    calculate_position_size,
    update_peak_price,
    close_position,
    get_open_positions,
    InsufficientDataError,
    SENTIMENT_THRESHOLD,
    POSITION_HOLD_MINUTES,
    STOP_LOSS_PERCENT,
    MAX_POSITION_SIZE_ILS
)


def test_should_buy_positive_high_confidence():
    """Test buy signal with POSITIVE sentiment and high confidence"""
    should, size, reason = should_buy('POSITIVE', 0.85, 100.0, 1000000.0)

    assert should is True
    assert size == 5000.0  # MIN(1% of 1M, 5000) = 5000
    assert 'POSITIVE' in reason
    assert '0.85' in reason


def test_should_buy_positive_exact_threshold():
    """Test buy signal at exact confidence threshold"""
    should, size, reason = should_buy('POSITIVE', SENTIMENT_THRESHOLD, 50.0)

    assert should is True
    assert size == MAX_POSITION_SIZE_ILS


def test_should_buy_positive_below_threshold():
    """Test no buy when confidence below threshold"""
    should, size, reason = should_buy('POSITIVE', 0.65, 100.0)

    assert should is False
    assert size is None
    assert 'below threshold' in reason


def test_should_buy_negative_sentiment():
    """Test no buy with NEGATIVE sentiment"""
    should, size, reason = should_buy('NEGATIVE', 0.95, 100.0)

    assert should is False
    assert size is None
    assert 'NEGATIVE' in reason


def test_should_buy_neutral_sentiment():
    """Test no buy with NEUTRAL sentiment"""
    should, size, reason = should_buy('NEUTRAL', 0.80, 100.0)

    assert should is False
    assert size is None
    assert 'NEUTRAL' in reason


def test_should_buy_missing_sentiment():
    """Test error when sentiment is missing"""
    with pytest.raises(InsufficientDataError, match="Sentiment is required"):
        should_buy('', 0.85, 100.0)


def test_should_buy_invalid_price():
    """Test error when price is invalid"""
    with pytest.raises(InsufficientDataError, match="Valid current price is required"):
        should_buy('POSITIVE', 0.85, 0.0)


def test_should_sell_time_limit():
    """Test sell trigger at 60-minute time limit"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
    current_time = entry_time + timedelta(minutes=POSITION_HOLD_MINUTES)

    should, reason = should_sell(
        entry_time=entry_time,
        entry_price=100.0,
        peak_price=105.0,
        current_price=103.0,
        current_time=current_time
    )

    assert should is True
    assert 'Time limit reached' in reason
    assert '60min' in reason


def test_should_sell_time_limit_with_profit():
    """Test time-based sell shows profit percentage"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
    current_time = entry_time + timedelta(minutes=60)

    should, reason = should_sell(
        entry_time=entry_time,
        entry_price=100.0,
        peak_price=105.0,
        current_price=103.0,  # +3% profit
        current_time=current_time
    )

    assert should is True
    assert '+3.00%' in reason


def test_should_sell_stop_loss_exact():
    """Test sell trigger at exact -1% stop loss"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
    current_time = entry_time + timedelta(minutes=30)

    peak_price = 100.0
    current_price = peak_price * (1 - STOP_LOSS_PERCENT)  # Exactly -1%

    should, reason = should_sell(
        entry_time=entry_time,
        entry_price=95.0,
        peak_price=peak_price,
        current_price=current_price,
        current_time=current_time
    )

    assert should is True
    assert 'Stop loss triggered' in reason


def test_should_sell_stop_loss_exceeded():
    """Test sell trigger when drop exceeds -1%"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
    current_time = entry_time + timedelta(minutes=20)

    should, reason = should_sell(
        entry_time=entry_time,
        entry_price=100.0,
        peak_price=110.0,
        current_price=107.0,  # -2.73% from peak
        current_time=current_time
    )

    assert should is True
    assert 'Stop loss triggered' in reason
    assert 'drop from peak' in reason


def test_should_sell_hold_position():
    """Test no sell when conditions not met"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
    current_time = entry_time + timedelta(minutes=30)

    should, reason = should_sell(
        entry_time=entry_time,
        entry_price=100.0,
        peak_price=105.0,
        current_price=104.5,  # Only -0.48% from peak
        current_time=current_time
    )

    assert should is False
    assert 'Hold position' in reason


def test_should_sell_invalid_prices():
    """Test error with invalid prices"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))

    with pytest.raises(InsufficientDataError, match="All prices must be positive"):
        should_sell(entry_time, 0.0, 100.0, 100.0)


def test_should_sell_peak_below_entry():
    """Test error when peak price below entry price"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    entry_time = israel_tz.localize(datetime(2024, 3, 31, 10, 0))

    with pytest.raises(InsufficientDataError, match="Peak price cannot be less than entry price"):
        should_sell(entry_time, 100.0, 95.0, 90.0)


def test_calculate_position_size_volume_based():
    """Test position size calculation with volume data"""
    # 1% of 800,000 = 8,000, capped at 5,000
    size = calculate_position_size(100.0, 800000.0)
    assert size == MAX_POSITION_SIZE_ILS


def test_calculate_position_size_volume_below_max():
    """Test position size when 1% of volume is below max"""
    # 1% of 300,000 = 3,000
    size = calculate_position_size(100.0, 300000.0)
    assert size == 3000.0


def test_calculate_position_size_no_volume():
    """Test position size defaults to max when no volume data"""
    size = calculate_position_size(100.0, None)
    assert size == MAX_POSITION_SIZE_ILS


def test_calculate_position_size_zero_volume():
    """Test position size with zero volume"""
    size = calculate_position_size(100.0, 0.0)
    assert size == MAX_POSITION_SIZE_ILS


def test_update_peak_price():
    """Test updating peak price in database"""
    with patch('lib.trading_logic.get_supabase_client') as mock_client:
        mock_table = Mock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock()

        update_peak_price('position-123', 150.0)

        mock_table.update.assert_called_once_with({'peak_price': 150.0})
        mock_table.eq.assert_called_once_with('id', 'position-123')


def test_close_position():
    """Test closing a position"""
    with patch('lib.trading_logic.get_supabase_client') as mock_client, \
         patch('lib.trading_logic.get_israel_time') as mock_time:

        israel_tz = pytz.timezone('Asia/Jerusalem')
        mock_time.return_value = israel_tz.localize(datetime(2024, 3, 31, 12, 0))

        # Create separate mock instances for select and update chains
        mock_select_chain = Mock()
        mock_update_chain = Mock()

        # Mock table() to return different chains based on subsequent calls
        mock_client.return_value.table.return_value = mock_select_chain

        # Mock select query chain
        mock_select_chain.select.return_value = mock_select_chain
        mock_select_chain.eq.return_value = mock_select_chain
        mock_select_chain.single.return_value = mock_select_chain
        mock_select_chain.execute.return_value = Mock(data={
            'id': 'pos-123',
            'entry_price': 100.0,
            'position_size_ils': 5000.0
        })

        # Mock update query chain (will be returned on second table() call)
        mock_select_chain.update.return_value = mock_update_chain
        mock_update_chain.eq.return_value = mock_update_chain
        mock_update_chain.execute.return_value = Mock(data=[{
            'id': 'pos-123',
            'exit_price': 105.0,
            'profit_loss_ils': 250.0,
            'profit_loss_percent': 5.0
        }])

        result = close_position('pos-123', 105.0, 'Time limit reached')

        assert result['exit_price'] == 105.0
        assert result['profit_loss_ils'] == 250.0


def test_get_open_positions():
    """Test fetching open positions"""
    with patch('lib.trading_logic.get_supabase_client') as mock_client:
        mock_table = Mock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.is_.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[
            {'id': 'pos-1', 'ticker': 'TSEM.TA'},
            {'id': 'pos-2', 'ticker': 'TEVA.TA'}
        ])

        positions = get_open_positions()

        assert len(positions) == 2
        assert positions[0]['id'] == 'pos-1'
        mock_table.is_.assert_called_once_with('exit_time', 'null')
