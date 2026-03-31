"""
Email notification serverless function.

Sends email alerts for:
- New positions created (BUY alerts)
- Positions closed (SELL alerts)

Uses Resend API for delivery.
"""

from typing import Dict, Any, Optional
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.db import log_system_event

# Will import resend when needed
try:
    import resend
except ImportError:
    resend = None


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_POST(self):
        """Handle POST request to send email"""
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            params = json.loads(body.decode('utf-8'))

            result = send_trade_alert_email(
                alert_type=params.get('alert_type'),
                ticker=params.get('ticker'),
                company_name=params.get('company_name'),
                price=params.get('price'),
                position_size=params.get('position_size'),
                reason=params.get('reason'),
                profit_loss_ils=params.get('profit_loss_ils'),
                profit_loss_percent=params.get('profit_loss_percent')
            )

            self.send_response(200 if result['success'] else 500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            log_system_event('ERROR', 'send_email', f"Function failed: {e}", {})

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())


def send_trade_alert_email(
    alert_type: str,
    ticker: str,
    company_name: str,
    price: float,
    position_size: float,
    reason: str,
    profit_loss_ils: Optional[float] = None,
    profit_loss_percent: Optional[float] = None
) -> Dict[str, Any]:
    """
    Send trade alert email using Resend.

    Args:
        alert_type: 'BUY' or 'SELL'
        ticker: Stock ticker
        company_name: Company name
        price: Entry/exit price
        position_size: Position size in ILS
        reason: Reason for trade
        profit_loss_ils: P/L in ILS (SELL only)
        profit_loss_percent: P/L percentage (SELL only)

    Returns:
        Dict with success status and message
    """
    # Check if Resend is available and configured
    api_key = os.getenv('RESEND_API_KEY')
    recipient_email = os.getenv('ALERT_EMAIL')

    if not resend or not api_key:
        log_system_event(
            'WARNING',
            'send_email',
            'Email sending disabled: Resend not configured',
            {}
        )
        return {
            'success': False,
            'message': 'Email sending not configured (Resend API key missing)'
        }

    if not recipient_email:
        log_system_event(
            'WARNING',
            'send_email',
            'Email sending disabled: No recipient configured',
            {}
        )
        return {
            'success': False,
            'message': 'No recipient email configured'
        }

    # Build email content
    if alert_type == 'BUY':
        subject = f"🟢 BUY Alert: {ticker} - {company_name}"
        body = f"""
<h2>New Position Opened</h2>
<p><strong>Ticker:</strong> {ticker}</p>
<p><strong>Company:</strong> {company_name}</p>
<p><strong>Entry Price:</strong> ₪{price:.2f}</p>
<p><strong>Position Size:</strong> ₪{position_size:.2f}</p>
<p><strong>Reason:</strong> {reason}</p>
"""
    elif alert_type == 'SELL':
        pl_indicator = "🟢" if profit_loss_ils >= 0 else "🔴"
        subject = f"{pl_indicator} SELL Alert: {ticker} - {company_name}"
        body = f"""
<h2>Position Closed</h2>
<p><strong>Ticker:</strong> {ticker}</p>
<p><strong>Company:</strong> {company_name}</p>
<p><strong>Exit Price:</strong> ₪{price:.2f}</p>
<p><strong>Position Size:</strong> ₪{position_size:.2f}</p>
<p><strong>Profit/Loss:</strong> ₪{profit_loss_ils:+.2f} ({profit_loss_percent:+.2f}%)</p>
<p><strong>Reason:</strong> {reason}</p>
"""
    else:
        return {
            'success': False,
            'message': f'Invalid alert_type: {alert_type}'
        }

    # Send email
    try:
        resend.api_key = api_key

        params = {
            "from": "TASE Trading <noreply@trading.example.com>",
            "to": [recipient_email],
            "subject": subject,
            "html": body
        }

        email_result = resend.Emails.send(params)

        log_system_event(
            'INFO',
            'send_email',
            f"Sent {alert_type} alert for {ticker}",
            {
                'alert_type': alert_type,
                'ticker': ticker,
                'email_id': email_result.get('id')
            }
        )

        return {
            'success': True,
            'message': f'{alert_type} alert sent successfully',
            'email_id': email_result.get('id')
        }

    except Exception as e:
        log_system_event(
            'ERROR',
            'send_email',
            f"Failed to send email: {e}",
            {
                'alert_type': alert_type,
                'ticker': ticker,
                'error': str(e)
            }
        )
        return {
            'success': False,
            'message': f'Failed to send email: {e}'
        }
