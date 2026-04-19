"""
IBKR status API endpoint.

Returns current trading mode and connection status.
Vercel serverless function handler.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.ibkr_client import get_ibkr_client, IBKRConnectionError


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_GET(self):
        """Handle GET request for IBKR status"""
        try:
            trading_mode = os.environ.get('TRADING_MODE', 'DRY_RUN').upper()

            status = {
                'trading_mode': trading_mode,
                'connected': False,
                'account': None,
                'gateway_host': os.environ.get('IBKR_GATEWAY_HOST', '127.0.0.1'),
            }

            if trading_mode == 'DRY_RUN':
                status['connected'] = True
                status['account'] = 'DRY_RUN_ACCOUNT'
                status['message'] = 'Simulated mode - no real orders'
            else:
                try:
                    client = get_ibkr_client(trading_mode)
                    if client.connect(timeout=5):
                        status['connected'] = True
                        status['account'] = client.get_account()
                        status['message'] = f'{trading_mode} trading active'
                        client.disconnect()
                    else:
                        status['message'] = 'Failed to connect to IB Gateway'
                except IBKRConnectionError as e:
                    status['message'] = f'Connection error: {str(e)}'
                except Exception as e:
                    status['message'] = f'Error: {str(e)}'

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
