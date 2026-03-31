import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.send_email import send_trade_alert_email


@pytest.fixture
def mock_dependencies():
    """Mock external dependencies"""
    with patch('api.send_email.log_system_event') as mock_log, \
         patch('api.send_email.resend') as mock_resend:

        yield {
            'log': mock_log,
            'resend': mock_resend
        }


def test_send_buy_alert_success(mock_dependencies):
    """Test successful BUY alert email"""
    with patch.dict(os.environ, {
        'RESEND_API_KEY': 'test_api_key',
        'ALERT_EMAIL': 'test@example.com'
    }):
        mock_dependencies['resend'].Emails.send.return_value = {'id': 'email-123'}

        result = send_trade_alert_email(
            alert_type='BUY',
            ticker='TSEM.TA',
            company_name='Tower Semiconductor',
            price=42.50,
            position_size=5000.0,
            reason='POSITIVE sentiment with 0.85 confidence'
        )

        assert result['success'] is True
        assert 'BUY alert sent' in result['message']
        assert result['email_id'] == 'email-123'
        mock_dependencies['resend'].Emails.send.assert_called_once()


def test_send_sell_alert_success(mock_dependencies):
    """Test successful SELL alert email"""
    with patch.dict(os.environ, {
        'RESEND_API_KEY': 'test_api_key',
        'ALERT_EMAIL': 'test@example.com'
    }):
        mock_dependencies['resend'].Emails.send.return_value = {'id': 'email-456'}

        result = send_trade_alert_email(
            alert_type='SELL',
            ticker='TEVA.TA',
            company_name='Teva Pharmaceutical',
            price=51.0,
            position_size=5000.0,
            reason='Time limit reached (60min)',
            profit_loss_ils=250.0,
            profit_loss_percent=5.0
        )

        assert result['success'] is True
        assert 'SELL alert sent' in result['message']
        assert result['email_id'] == 'email-456'

        # Verify email content includes P/L
        call_args = mock_dependencies['resend'].Emails.send.call_args[0][0]
        assert '₪+250.00' in call_args['html']
        assert '+5.00%' in call_args['html']


def test_send_email_no_api_key(mock_dependencies):
    """Test email sending without API key"""
    with patch.dict(os.environ, {}, clear=True):
        result = send_trade_alert_email(
            alert_type='BUY',
            ticker='TSEM.TA',
            company_name='Tower Semiconductor',
            price=42.50,
            position_size=5000.0,
            reason='Test'
        )

        assert result['success'] is False
        assert 'not configured' in result['message']


def test_send_email_no_recipient(mock_dependencies):
    """Test email sending without recipient"""
    with patch.dict(os.environ, {'RESEND_API_KEY': 'test_key'}):
        result = send_trade_alert_email(
            alert_type='BUY',
            ticker='TSEM.TA',
            company_name='Tower Semiconductor',
            price=42.50,
            position_size=5000.0,
            reason='Test'
        )

        assert result['success'] is False
        assert 'No recipient' in result['message']


def test_send_email_invalid_alert_type(mock_dependencies):
    """Test with invalid alert type"""
    with patch.dict(os.environ, {
        'RESEND_API_KEY': 'test_key',
        'ALERT_EMAIL': 'test@example.com'
    }):
        result = send_trade_alert_email(
            alert_type='INVALID',
            ticker='TSEM.TA',
            company_name='Tower Semiconductor',
            price=42.50,
            position_size=5000.0,
            reason='Test'
        )

        assert result['success'] is False
        assert 'Invalid alert_type' in result['message']


def test_send_email_api_error(mock_dependencies):
    """Test handling of Resend API errors"""
    with patch.dict(os.environ, {
        'RESEND_API_KEY': 'test_key',
        'ALERT_EMAIL': 'test@example.com'
    }):
        mock_dependencies['resend'].Emails.send.side_effect = Exception("API Error")

        result = send_trade_alert_email(
            alert_type='BUY',
            ticker='TSEM.TA',
            company_name='Tower Semiconductor',
            price=42.50,
            position_size=5000.0,
            reason='Test'
        )

        assert result['success'] is False
        assert 'Failed to send email' in result['message']


def test_sell_alert_negative_pl(mock_dependencies):
    """Test SELL alert with negative profit/loss"""
    with patch.dict(os.environ, {
        'RESEND_API_KEY': 'test_key',
        'ALERT_EMAIL': 'test@example.com'
    }):
        mock_dependencies['resend'].Emails.send.return_value = {'id': 'email-789'}

        result = send_trade_alert_email(
            alert_type='SELL',
            ticker='ICL.TA',
            company_name='ICL Group',
            price=73.0,
            position_size=5000.0,
            reason='Stop loss triggered',
            profit_loss_ils=-100.0,
            profit_loss_percent=-2.0
        )

        assert result['success'] is True

        # Verify negative P/L formatting
        call_args = mock_dependencies['resend'].Emails.send.call_args[0][0]
        assert '₪-100.00' in call_args['html']
        assert '-2.00%' in call_args['html']
