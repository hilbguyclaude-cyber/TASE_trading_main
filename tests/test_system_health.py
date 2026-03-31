import pytest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch
from lib.system_health import (
    HealthCheckResult,
    check_gemini_health,
    check_yfinance_health,
    check_tase_scraper_health,
    check_database_health,
    run_full_health_check,
    update_system_health_status,
    should_run_health_check,
    HEALTH_CHECK_COOLDOWN_MINUTES
)


def test_health_check_result():
    """Test HealthCheckResult creation"""
    with patch('lib.system_health.get_israel_time') as mock_time:
        israel_tz = pytz.timezone('Asia/Jerusalem')
        mock_time.return_value = israel_tz.localize(datetime(2024, 3, 31, 10, 0))

        result = HealthCheckResult('test_service', True)

        assert result.service == 'test_service'
        assert result.healthy is True
        assert result.error is None
        assert result.timestamp is not None


def test_check_gemini_health_success():
    """Test Gemini health check success"""
    with patch('lib.system_health.analyze_announcement_sentiment') as mock_analyze:
        mock_analyze.return_value = {
            'sentiment': 'POSITIVE',
            'confidence': 0.85,
            'reasoning': 'Test reasoning'
        }

        result = check_gemini_health()

        assert result.healthy is True
        assert result.service == 'gemini'
        assert result.error is None


def test_check_gemini_health_invalid_response():
    """Test Gemini health check with invalid response"""
    with patch('lib.system_health.analyze_announcement_sentiment') as mock_analyze:
        mock_analyze.return_value = {'invalid': 'response'}

        result = check_gemini_health()

        assert result.healthy is False
        assert 'Invalid response structure' in result.error


def test_check_gemini_health_rate_limit():
    """Test Gemini health check with rate limit error"""
    from lib.gemini_client import GeminiRateLimitError

    with patch('lib.system_health.analyze_announcement_sentiment') as mock_analyze:
        mock_analyze.side_effect = GeminiRateLimitError("Rate limit exceeded")

        result = check_gemini_health()

        assert result.healthy is False
        assert 'Rate limit' in result.error


def test_check_gemini_health_auth_error():
    """Test Gemini health check with auth error"""
    from lib.gemini_client import GeminiAuthError

    with patch('lib.system_health.analyze_announcement_sentiment') as mock_analyze:
        mock_analyze.side_effect = GeminiAuthError("Invalid API key")

        result = check_gemini_health()

        assert result.healthy is False
        assert 'Auth error' in result.error


def test_check_yfinance_health_success():
    """Test Yahoo Finance health check success"""
    with patch('lib.system_health.get_current_price') as mock_price:
        mock_price.return_value = 42.50

        result = check_yfinance_health()

        assert result.healthy is True
        assert result.service == 'yfinance'


def test_check_yfinance_health_invalid_price():
    """Test Yahoo Finance health check with invalid price"""
    with patch('lib.system_health.get_current_price') as mock_price:
        mock_price.return_value = 0.0

        result = check_yfinance_health()

        assert result.healthy is False
        assert 'Invalid price' in result.error


def test_check_yfinance_health_fetch_error():
    """Test Yahoo Finance health check with fetch error"""
    from lib.yfinance_client import PriceFetchError

    with patch('lib.system_health.get_current_price') as mock_price:
        mock_price.side_effect = PriceFetchError("Connection failed")

        result = check_yfinance_health()

        assert result.healthy is False
        assert result.error is not None


def test_check_tase_scraper_health_success():
    """Test TASE scraper health check success"""
    with patch('lib.system_health.fetch_announcements') as mock_fetch:
        mock_fetch.return_value = [{
            'announcement_id': 'ANN001',
            'company_name': 'Test Company',
            'title': 'Test Title',
            'content': 'Test Content',
            'published_at': datetime.now()
        }]

        result = check_tase_scraper_health()

        assert result.healthy is True
        assert result.service == 'tase_scraper'


def test_check_tase_scraper_health_no_announcements():
    """Test TASE scraper health check with no results"""
    with patch('lib.system_health.fetch_announcements') as mock_fetch:
        mock_fetch.return_value = []

        result = check_tase_scraper_health()

        assert result.healthy is False
        assert 'No announcements' in result.error


def test_check_tase_scraper_health_invalid_structure():
    """Test TASE scraper health check with invalid structure"""
    with patch('lib.system_health.fetch_announcements') as mock_fetch:
        mock_fetch.return_value = [{'invalid': 'structure'}]

        result = check_tase_scraper_health()

        assert result.healthy is False
        assert 'Invalid announcement structure' in result.error


def test_check_tase_scraper_health_scraper_error():
    """Test TASE scraper health check with ScraperError"""
    from lib.tase_scraper import ScraperError

    with patch('lib.system_health.fetch_announcements') as mock_fetch:
        mock_fetch.side_effect = ScraperError("All methods failed")

        result = check_tase_scraper_health()

        assert result.healthy is False


def test_check_database_health_success():
    """Test database health check success"""
    with patch('lib.system_health.get_supabase_client') as mock_client:
        mock_table = Mock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{'id': 1}])

        result = check_database_health()

        assert result.healthy is True
        assert result.service == 'database'


def test_check_database_health_connection_error():
    """Test database health check with connection error"""
    with patch('lib.system_health.get_supabase_client') as mock_client:
        mock_client.side_effect = Exception("Connection failed")

        result = check_database_health()

        assert result.healthy is False


def test_run_full_health_check_all_healthy():
    """Test full health check with all services healthy"""
    with patch('lib.system_health.check_database_health') as mock_db, \
         patch('lib.system_health.check_gemini_health') as mock_gemini, \
         patch('lib.system_health.check_yfinance_health') as mock_yf, \
         patch('lib.system_health.check_tase_scraper_health') as mock_tase:

        mock_db.return_value = HealthCheckResult('database', True)
        mock_gemini.return_value = HealthCheckResult('gemini', True)
        mock_yf.return_value = HealthCheckResult('yfinance', True)
        mock_tase.return_value = HealthCheckResult('tase_scraper', True)

        result = run_full_health_check()

        assert result['overall_healthy'] is True
        assert len(result['unhealthy_services']) == 0
        assert 'services' in result


def test_run_full_health_check_some_unhealthy():
    """Test full health check with some services unhealthy"""
    with patch('lib.system_health.check_database_health') as mock_db, \
         patch('lib.system_health.check_gemini_health') as mock_gemini, \
         patch('lib.system_health.check_yfinance_health') as mock_yf, \
         patch('lib.system_health.check_tase_scraper_health') as mock_tase:

        mock_db.return_value = HealthCheckResult('database', True)
        mock_gemini.return_value = HealthCheckResult('gemini', False, "API error")
        mock_yf.return_value = HealthCheckResult('yfinance', True)
        mock_tase.return_value = HealthCheckResult('tase_scraper', False, "Scraper error")

        result = run_full_health_check()

        assert result['overall_healthy'] is False
        assert 'gemini' in result['unhealthy_services']
        assert 'tase_scraper' in result['unhealthy_services']


def test_update_system_health_status_healthy():
    """Test updating system status when all healthy"""
    with patch('lib.system_health.update_system_status') as mock_update, \
         patch('lib.system_health.log_system_event') as mock_log:

        health_result = {
            'overall_healthy': True,
            'unhealthy_services': [],
            'services': {},
            'timestamp': datetime.now(pytz.timezone('Asia/Jerusalem'))
        }

        update_system_health_status(health_result)

        mock_update.assert_called_once()
        update_call = mock_update.call_args[0][0]
        assert update_call['status'] == 'HEALTHY'
        assert update_call['buying_enabled'] is True


def test_update_system_health_status_database_down():
    """Test updating system status when database is down"""
    with patch('lib.system_health.update_system_status') as mock_update, \
         patch('lib.system_health.log_system_event') as mock_log:

        health_result = {
            'overall_healthy': False,
            'unhealthy_services': ['database'],
            'services': {'database': HealthCheckResult('database', False, "Connection failed")},
            'timestamp': datetime.now(pytz.timezone('Asia/Jerusalem'))
        }

        update_system_health_status(health_result)

        update_call = mock_update.call_args[0][0]
        assert update_call['status'] == 'DOWN'
        assert update_call['buying_enabled'] is False


def test_update_system_health_status_degraded():
    """Test updating system status when some services degraded"""
    with patch('lib.system_health.update_system_status') as mock_update, \
         patch('lib.system_health.log_system_event') as mock_log:

        health_result = {
            'overall_healthy': False,
            'unhealthy_services': ['yfinance'],
            'services': {'yfinance': HealthCheckResult('yfinance', False, "API error")},
            'timestamp': datetime.now(pytz.timezone('Asia/Jerusalem'))
        }

        update_system_health_status(health_result)

        update_call = mock_update.call_args[0][0]
        assert update_call['status'] == 'DEGRADED'
        # Buying should still be enabled (yfinance not critical for new positions)
        assert update_call['buying_enabled'] is True


def test_update_system_health_status_gemini_down():
    """Test that buying is disabled when Gemini is down"""
    with patch('lib.system_health.update_system_status') as mock_update, \
         patch('lib.system_health.log_system_event') as mock_log:

        health_result = {
            'overall_healthy': False,
            'unhealthy_services': ['gemini'],
            'services': {'gemini': HealthCheckResult('gemini', False, "API error")},
            'timestamp': datetime.now(pytz.timezone('Asia/Jerusalem'))
        }

        update_system_health_status(health_result)

        update_call = mock_update.call_args[0][0]
        assert update_call['status'] == 'DEGRADED'
        # Buying should be disabled (Gemini critical for new positions)
        assert update_call['buying_enabled'] is False


def test_should_run_health_check_no_previous():
    """Test health check should run when no previous check"""
    with patch('lib.system_health.get_supabase_client') as mock_client:
        mock_table = Mock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_table.execute.return_value = Mock(data={'last_check': None})

        should_run = should_run_health_check()

        assert should_run is True


def test_should_run_health_check_cooldown_not_expired():
    """Test health check should not run during cooldown"""
    with patch('lib.system_health.get_supabase_client') as mock_client, \
         patch('lib.system_health.get_israel_time') as mock_time:

        israel_tz = pytz.timezone('Asia/Jerusalem')
        now = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
        last_check = now - timedelta(minutes=2)  # 2 minutes ago (cooldown is 5)

        mock_time.return_value = now

        mock_table = Mock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_table.execute.return_value = Mock(data={'last_check': last_check.isoformat()})

        should_run = should_run_health_check()

        assert should_run is False


def test_should_run_health_check_cooldown_expired():
    """Test health check should run after cooldown expires"""
    with patch('lib.system_health.get_supabase_client') as mock_client, \
         patch('lib.system_health.get_israel_time') as mock_time:

        israel_tz = pytz.timezone('Asia/Jerusalem')
        now = israel_tz.localize(datetime(2024, 3, 31, 10, 0))
        last_check = now - timedelta(minutes=HEALTH_CHECK_COOLDOWN_MINUTES + 1)

        mock_time.return_value = now

        mock_table = Mock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.single.return_value = mock_table
        mock_table.execute.return_value = Mock(data={'last_check': last_check.isoformat()})

        should_run = should_run_health_check()

        assert should_run is True
