import pytest
from datetime import datetime
import pytz
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.cron.check_announcements import check_announcements


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies"""
    with patch('api.cron.check_announcements.should_run_health_check') as mock_health_check, \
         patch('api.cron.check_announcements.run_full_health_check') as mock_run_health, \
         patch('api.cron.check_announcements.update_system_health_status') as mock_update_health, \
         patch('api.cron.check_announcements.is_during_trading_hours') as mock_trading_hours, \
         patch('api.cron.check_announcements.get_system_status') as mock_system_status, \
         patch('api.cron.check_announcements.fetch_announcements') as mock_fetch, \
         patch('api.cron.check_announcements.deduplicate_announcements') as mock_dedup, \
         patch('api.cron.check_announcements.get_supabase_client') as mock_client, \
         patch('api.cron.check_announcements.lookup_ticker_by_company_name') as mock_lookup, \
         patch('api.cron.check_announcements.insert_unmapped_company') as mock_unmapped, \
         patch('api.cron.check_announcements.log_system_event') as mock_log:

        yield {
            'health_check': mock_health_check,
            'run_health': mock_run_health,
            'update_health': mock_update_health,
            'trading_hours': mock_trading_hours,
            'system_status': mock_system_status,
            'fetch': mock_fetch,
            'dedup': mock_dedup,
            'client': mock_client,
            'lookup': mock_lookup,
            'unmapped': mock_unmapped,
            'log': mock_log
        }


def test_check_announcements_outside_trading_hours(mock_dependencies):
    """Test cron job skips when outside trading hours"""
    mock_dependencies['health_check'].return_value = False
    mock_dependencies['trading_hours'].return_value = False

    result = check_announcements()

    assert result['success'] is True
    assert result['message'] == 'Outside trading hours'
    assert result['announcements_processed'] == 0
    mock_dependencies['fetch'].assert_not_called()


def test_check_announcements_system_down(mock_dependencies):
    """Test cron job skips when system is DOWN"""
    mock_dependencies['health_check'].return_value = False
    mock_dependencies['trading_hours'].return_value = True
    mock_dependencies['system_status'].return_value = {'status': 'DOWN'}

    result = check_announcements()

    assert result['success'] is False
    assert result['message'] == 'System is DOWN'
    assert result['announcements_processed'] == 0


def test_check_announcements_runs_health_check(mock_dependencies):
    """Test health check runs when cooldown expired"""
    mock_dependencies['health_check'].return_value = True
    mock_dependencies['run_health'].return_value = {'overall_healthy': True}
    mock_dependencies['trading_hours'].return_value = False

    check_announcements()

    mock_dependencies['run_health'].assert_called_once()
    mock_dependencies['update_health'].assert_called_once()


def test_check_announcements_success(mock_dependencies):
    """Test successful announcement processing"""
    # Setup mocks
    mock_dependencies['health_check'].return_value = False
    mock_dependencies['trading_hours'].return_value = True
    mock_dependencies['system_status'].return_value = {'status': 'HEALTHY'}

    # Mock announcements
    israel_tz = pytz.timezone('Asia/Jerusalem')
    announcements = [
        {
            'announcement_id': 'ANN001',
            'company_name': 'Tower Semiconductor',
            'title': 'Q1 Results',
            'content': 'Great quarter',
            'published_at': israel_tz.localize(datetime(2024, 3, 31, 10, 0)),
            'source_url': 'https://example.com/ann001',
            'raw_data': {}
        }
    ]

    mock_dependencies['fetch'].return_value = announcements
    mock_dependencies['dedup'].return_value = announcements

    # Mock database client
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table

    # Mock existing check (not found)
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])

    # Mock ticker lookup
    mock_dependencies['lookup'].return_value = 'TSEM.TA'

    # Mock insert
    mock_table.insert.return_value = mock_table

    result = check_announcements()

    assert result['success'] is True
    assert result['announcements_processed'] == 1
    assert result['announcements_fetched'] == 1
    mock_table.insert.assert_called_once()


def test_check_announcements_skips_existing(mock_dependencies):
    """Test that existing announcements are skipped"""
    mock_dependencies['health_check'].return_value = False
    mock_dependencies['trading_hours'].return_value = True
    mock_dependencies['system_status'].return_value = {'status': 'HEALTHY'}

    israel_tz = pytz.timezone('Asia/Jerusalem')
    announcements = [
        {
            'announcement_id': 'ANN001',
            'company_name': 'Tower Semiconductor',
            'title': 'Q1 Results',
            'content': 'Great quarter',
            'published_at': israel_tz.localize(datetime(2024, 3, 31, 10, 0)),
            'source_url': 'https://example.com/ann001',
            'raw_data': {}
        }
    ]

    mock_dependencies['fetch'].return_value = announcements
    mock_dependencies['dedup'].return_value = announcements

    # Mock database client - announcement already exists
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[{'id': 'existing'}])

    result = check_announcements()

    assert result['success'] is True
    assert result['announcements_processed'] == 0
    mock_table.insert.assert_not_called()


def test_check_announcements_unmapped_company(mock_dependencies):
    """Test that unmapped companies are queued"""
    mock_dependencies['health_check'].return_value = False
    mock_dependencies['trading_hours'].return_value = True
    mock_dependencies['system_status'].return_value = {'status': 'HEALTHY'}

    israel_tz = pytz.timezone('Asia/Jerusalem')
    announcements = [
        {
            'announcement_id': 'ANN001',
            'company_name': 'Unknown Company',
            'title': 'Some announcement',
            'content': 'Content',
            'published_at': israel_tz.localize(datetime(2024, 3, 31, 10, 0)),
            'source_url': 'https://example.com/ann001',
            'raw_data': {}
        }
    ]

    mock_dependencies['fetch'].return_value = announcements
    mock_dependencies['dedup'].return_value = announcements

    # Mock database client
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])

    # Mock ticker lookup - not found
    mock_dependencies['lookup'].return_value = None

    result = check_announcements()

    assert result['success'] is True
    assert 'Unknown Company' in result['unmapped_companies']
    mock_dependencies['unmapped'].assert_called_once()
    mock_table.insert.assert_not_called()


def test_check_announcements_fetch_error(mock_dependencies):
    """Test handling of fetch errors"""
    mock_dependencies['health_check'].return_value = False
    mock_dependencies['trading_hours'].return_value = True
    mock_dependencies['system_status'].return_value = {'status': 'HEALTHY'}
    mock_dependencies['fetch'].side_effect = Exception("Network error")

    result = check_announcements()

    assert result['success'] is False
    assert 'Failed to fetch announcements' in result['message']
    assert result['announcements_processed'] == 0
