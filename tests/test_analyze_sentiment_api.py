import pytest
from datetime import datetime
import pytz
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.analyze_sentiment import analyze_pending_sentiments


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies"""
    with patch('api.analyze_sentiment.get_system_status') as mock_status, \
         patch('api.analyze_sentiment.get_supabase_client') as mock_client, \
         patch('api.analyze_sentiment.analyze_announcement_sentiment') as mock_analyze, \
         patch('api.analyze_sentiment.should_buy') as mock_should_buy, \
         patch('api.analyze_sentiment.get_price_with_fallback') as mock_price, \
         patch('api.analyze_sentiment.get_israel_time') as mock_time, \
         patch('api.analyze_sentiment.log_system_event') as mock_log:

        israel_tz = pytz.timezone('Asia/Jerusalem')
        mock_time.return_value = israel_tz.localize(datetime(2024, 3, 31, 10, 0))

        yield {
            'status': mock_status,
            'client': mock_client,
            'analyze': mock_analyze,
            'should_buy': mock_should_buy,
            'price': mock_price,
            'time': mock_time,
            'log': mock_log
        }


def test_analyze_pending_sentiments_system_down(mock_dependencies):
    """Test function skips when system is DOWN"""
    mock_dependencies['status'].return_value = {'status': 'DOWN', 'buying_enabled': False}

    result = analyze_pending_sentiments()

    assert result['success'] is False
    assert result['message'] == 'System is DOWN'
    assert result['analyzed'] == 0


def test_analyze_pending_sentiments_no_pending(mock_dependencies):
    """Test function with no pending announcements"""
    mock_dependencies['status'].return_value = {'status': 'HEALTHY', 'buying_enabled': True}

    # Mock database query - no results
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])

    result = analyze_pending_sentiments()

    assert result['success'] is True
    assert result['message'] == 'No pending announcements'
    assert result['analyzed'] == 0


def test_analyze_pending_sentiments_success_no_position(mock_dependencies):
    """Test successful analysis without position creation"""
    mock_dependencies['status'].return_value = {'status': 'HEALTHY', 'buying_enabled': True}

    # Mock pending announcement
    announcements = [{
        'id': 'ann-123',
        'announcement_id': 'ANN001',
        'company_name': 'Tower Semiconductor',
        'ticker': 'TSEM.TA',
        'title': 'Quarterly Results',
        'content': 'Mixed results this quarter'
    }]

    # Mock database query
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = Mock(data=announcements)

    # Mock sentiment analysis - NEUTRAL
    mock_dependencies['analyze'].return_value = {
        'sentiment': 'NEUTRAL',
        'confidence': 0.80,
        'reasoning': 'Mixed signals'
    }

    # Mock update
    mock_table.update.return_value = mock_table

    # Mock should_buy - no buy
    mock_dependencies['should_buy'].return_value = (False, None, "NEUTRAL sentiment")

    result = analyze_pending_sentiments()

    assert result['success'] is True
    assert result['analyzed'] == 1
    assert result['positions_created'] == 0
    mock_table.update.assert_called()


def test_analyze_pending_sentiments_creates_position(mock_dependencies):
    """Test successful analysis with position creation"""
    mock_dependencies['status'].return_value = {'status': 'HEALTHY', 'buying_enabled': True}

    # Mock pending announcement
    announcements = [{
        'id': 'ann-123',
        'announcement_id': 'ANN001',
        'company_name': 'Tower Semiconductor',
        'ticker': 'TSEM.TA',
        'title': 'Quarterly Results',
        'content': 'Excellent results this quarter'
    }]

    # Mock database
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = Mock(data=announcements)
    mock_table.update.return_value = mock_table
    mock_table.insert.return_value = mock_table

    # Mock sentiment analysis - POSITIVE
    mock_dependencies['analyze'].return_value = {
        'sentiment': 'POSITIVE',
        'confidence': 0.85,
        'reasoning': 'Strong positive signals'
    }

    # Mock should_buy - yes
    mock_dependencies['should_buy'].return_value = (True, 5000.0, "POSITIVE sentiment")

    # Mock price fetch
    mock_dependencies['price'].return_value = 42.50

    result = analyze_pending_sentiments()

    assert result['success'] is True
    assert result['analyzed'] == 1
    assert result['positions_created'] == 1
    mock_table.insert.assert_called_once()


def test_analyze_pending_sentiments_buying_disabled(mock_dependencies):
    """Test that positions are not created when buying disabled"""
    mock_dependencies['status'].return_value = {'status': 'DEGRADED', 'buying_enabled': False}

    # Mock pending announcement
    announcements = [{
        'id': 'ann-123',
        'announcement_id': 'ANN001',
        'company_name': 'Tower Semiconductor',
        'ticker': 'TSEM.TA',
        'title': 'Quarterly Results',
        'content': 'Excellent results'
    }]

    # Mock database
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = Mock(data=announcements)
    mock_table.update.return_value = mock_table

    # Mock sentiment analysis - POSITIVE
    mock_dependencies['analyze'].return_value = {
        'sentiment': 'POSITIVE',
        'confidence': 0.85,
        'reasoning': 'Strong positive signals'
    }

    result = analyze_pending_sentiments()

    assert result['success'] is True
    assert result['analyzed'] == 1
    assert result['positions_created'] == 0  # No position created (buying disabled)


def test_analyze_pending_sentiments_gemini_rate_limit(mock_dependencies):
    """Test handling of Gemini rate limit errors"""
    from lib.gemini_client import GeminiRateLimitError

    mock_dependencies['status'].return_value = {'status': 'HEALTHY', 'buying_enabled': True}

    # Mock pending announcements
    announcements = [
        {'id': 'ann-1', 'announcement_id': 'ANN001', 'company_name': 'Company 1', 'ticker': 'COMP1.TA', 'title': 'Title 1', 'content': 'Content 1'},
        {'id': 'ann-2', 'announcement_id': 'ANN002', 'company_name': 'Company 2', 'ticker': 'COMP2.TA', 'title': 'Title 2', 'content': 'Content 2'}
    ]

    # Mock database
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = Mock(data=announcements)

    # Mock rate limit on first call
    mock_dependencies['analyze'].side_effect = GeminiRateLimitError("Rate limit exceeded")

    result = analyze_pending_sentiments()

    assert result['success'] is True
    assert result['analyzed'] == 0  # Stopped at first error
    assert len(result['errors']) == 1
    assert 'Gemini API error' in result['errors'][0]


def test_analyze_pending_sentiments_max_limit(mock_dependencies):
    """Test max_announcements parameter"""
    mock_dependencies['status'].return_value = {'status': 'HEALTHY', 'buying_enabled': False}

    # Mock database - should be called with limit(5)
    mock_table = Mock()
    mock_dependencies['client'].return_value.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])

    analyze_pending_sentiments(max_announcements=5)

    mock_table.limit.assert_called_with(5)
