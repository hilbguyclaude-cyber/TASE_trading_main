import pytest
from datetime import datetime
import pytz
from lib.db import (
    get_supabase_client,
    log_system_event,
    get_system_status,
    is_during_trading_hours,
    get_israel_time
)

def test_supabase_connection():
    """Test Supabase client connects successfully"""
    client = get_supabase_client()
    assert client is not None
    # Test query
    result = client.table('system_status').select('*').execute()
    assert result.data is not None

def test_log_system_event():
    """Test logging system events"""
    log_system_event('INFO', 'test_component', 'Test message', {'key': 'value'})

    # Verify log was created
    client = get_supabase_client()
    result = client.table('system_logs')\
        .select('*')\
        .eq('component', 'test_component')\
        .order('created_at', desc=True)\
        .limit(1)\
        .execute()

    assert len(result.data) > 0
    assert result.data[0]['message'] == 'Test message'
    assert result.data[0]['metadata']['key'] == 'value'

def test_get_system_status():
    """Test fetching system status"""
    status = get_system_status()
    assert status is not None
    assert 'status' in status
    assert status['status'] in ['HEALTHY', 'DEGRADED', 'DOWN']
    assert 'buying_enabled' in status

def test_get_israel_time():
    """Test Israel timezone helper"""
    israel_time = get_israel_time()
    assert israel_time.tzinfo is not None
    assert str(israel_time.tzinfo) == 'Asia/Jerusalem'

def test_is_during_trading_hours():
    """Test trading hours detection"""
    israel_tz = pytz.timezone('Asia/Jerusalem')

    # Sunday 11:00 Israel time - should be True
    sunday_11am = israel_tz.localize(datetime(2024, 3, 31, 11, 0))  # Sunday
    # Use monkeypatch to test specific times would require changes to is_during_trading_hours
    # For now, just test the function exists and returns a boolean
    result = is_during_trading_hours()
    assert isinstance(result, bool)

    # Test with specific times by temporarily replacing get_israel_time
    from unittest.mock import patch

    # Sunday 11:00 Israel time - should be True (trading day, during hours)
    with patch('lib.db.get_israel_time', return_value=sunday_11am):
        assert is_during_trading_hours() == True

    # Friday 11:00 Israel time - should be True (shortened trading day, during hours)
    friday_11am = israel_tz.localize(datetime(2024, 3, 29, 11, 0))  # Friday
    with patch('lib.db.get_israel_time', return_value=friday_11am):
        assert is_during_trading_hours() == True

    # Friday 15:00 Israel time - should be False (after 14:30 Friday close)
    friday_3pm = israel_tz.localize(datetime(2024, 3, 29, 15, 0))  # Friday
    with patch('lib.db.get_israel_time', return_value=friday_3pm):
        assert is_during_trading_hours() == False

    # Saturday 11:00 Israel time - should be False (non-trading day)
    saturday_11am = israel_tz.localize(datetime(2024, 3, 30, 11, 0))  # Saturday
    with patch('lib.db.get_israel_time', return_value=saturday_11am):
        assert is_during_trading_hours() == False

    # Monday 09:30 Israel time - should be False (before 09:59)
    monday_930am = israel_tz.localize(datetime(2024, 4, 1, 9, 30))
    with patch('lib.db.get_israel_time', return_value=monday_930am):
        assert is_during_trading_hours() == False

    # Monday 17:30 Israel time - should be False (after 17:25)
    monday_530pm = israel_tz.localize(datetime(2024, 4, 1, 17, 30))
    with patch('lib.db.get_israel_time', return_value=monday_530pm):
        assert is_during_trading_hours() == False

def test_log_system_event_validation():
    """Test log level validation"""
    with pytest.raises(ValueError, match="Invalid log level"):
        log_system_event('INVALID', 'test_component', 'Test message')
