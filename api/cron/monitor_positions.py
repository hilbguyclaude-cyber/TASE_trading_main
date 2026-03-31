"""
Position monitor cron job.

Runs every minute (via Vercel cron) to:
1. Fetch all open positions
2. Get current prices
3. Update peak prices
4. Check sell conditions (60min OR -1% from peak)
5. Close positions and send notifications

Vercel serverless function handler.
"""

from datetime import datetime
from typing import Dict, Any, List
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from lib.db import (
    get_supabase_client,
    log_system_event,
    get_system_status,
    get_israel_time
)
from lib.yfinance_client import get_price_with_fallback, PriceFetchError
from lib.trading_logic import (
    get_open_positions,
    should_sell,
    update_peak_price,
    close_position
)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_GET(self):
        """Handle GET request from Vercel cron"""
        try:
            result = monitor_positions()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            log_system_event('ERROR', 'monitor_positions_cron', f"Cron job failed: {e}", {})

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())


def monitor_positions() -> Dict[str, Any]:
    """
    Main cron job logic for monitoring positions.

    Returns:
        Dict with execution summary
    """
    start_time = datetime.utcnow()

    log_system_event('INFO', 'monitor_positions_cron', 'Cron job started', {})

    # Fetch open positions
    try:
        open_positions = get_open_positions()
    except Exception as e:
        log_system_event('ERROR', 'monitor_positions_cron', f"Failed to fetch positions: {e}", {})
        return {
            'success': False,
            'message': f'Failed to fetch positions: {e}',
            'positions_checked': 0,
            'positions_closed': 0
        }

    if not open_positions:
        log_system_event('INFO', 'monitor_positions_cron', 'No open positions to monitor', {})
        return {
            'success': True,
            'message': 'No open positions',
            'positions_checked': 0,
            'positions_closed': 0
        }

    log_system_event(
        'INFO',
        'monitor_positions_cron',
        f"Monitoring {len(open_positions)} open positions",
        {'count': len(open_positions)}
    )

    # Monitor each position
    positions_checked = 0
    positions_closed = 0
    peak_updates = 0
    errors = []

    current_time = get_israel_time()

    for position in open_positions:
        try:
            ticker = position['ticker']
            position_id = position['id']
            entry_price = float(position['entry_price'])
            peak_price = float(position['peak_price'])
            entry_time = datetime.fromisoformat(position['entry_time'])

            # Get current price
            try:
                current_price = get_price_with_fallback(
                    ticker,
                    fallback_price=entry_price  # Fallback to entry price if fetch fails
                )
            except PriceFetchError as e:
                log_system_event(
                    'WARNING',
                    'monitor_positions_cron',
                    f"Failed to fetch price for {ticker}, using entry price as fallback",
                    {'position_id': position_id, 'error': str(e)}
                )
                current_price = entry_price

            positions_checked += 1

            # Update peak price if current is higher
            if current_price > peak_price:
                update_peak_price(position_id, current_price)
                peak_price = current_price
                peak_updates += 1

                log_system_event(
                    'INFO',
                    'monitor_positions_cron',
                    f"Updated peak price for {ticker}: {peak_price:.2f}",
                    {
                        'position_id': position_id,
                        'ticker': ticker,
                        'new_peak': peak_price
                    }
                )

            # Check if we should sell
            should_exit, exit_reason = should_sell(
                entry_time=entry_time,
                entry_price=entry_price,
                peak_price=peak_price,
                current_price=current_price,
                current_time=current_time
            )

            if should_exit:
                # Close position
                closed_position = close_position(position_id, current_price, exit_reason)
                positions_closed += 1

                profit_loss_percent = closed_position['profit_loss_percent']
                profit_loss_ils = closed_position['profit_loss_ils']

                log_system_event(
                    'INFO',
                    'monitor_positions_cron',
                    f"Closed position {ticker}: {exit_reason}. P/L: ₪{profit_loss_ils:+.2f} ({profit_loss_percent:+.2f}%)",
                    {
                        'position_id': position_id,
                        'ticker': ticker,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'profit_loss_ils': profit_loss_ils,
                        'profit_loss_percent': profit_loss_percent,
                        'exit_reason': exit_reason
                    }
                )

                # TODO: Send email notification (Task 12)

        except Exception as e:
            log_system_event(
                'ERROR',
                'monitor_positions_cron',
                f"Failed to process position {position.get('id')}: {e}",
                {'position': position}
            )
            errors.append(f"Failed to process position {position.get('ticker')}: {e}")

    # Summary
    execution_time = (datetime.utcnow() - start_time).total_seconds()

    log_system_event(
        'INFO',
        'monitor_positions_cron',
        f"Completed: {positions_checked} checked, {positions_closed} closed",
        {
            'positions_checked': positions_checked,
            'positions_closed': positions_closed,
            'peak_updates': peak_updates,
            'errors': len(errors),
            'execution_time_seconds': execution_time
        }
    )

    return {
        'success': True,
        'message': f'Monitored {positions_checked} positions, closed {positions_closed}',
        'positions_checked': positions_checked,
        'positions_closed': positions_closed,
        'peak_updates': peak_updates,
        'errors': errors,
        'execution_time_seconds': execution_time
    }
