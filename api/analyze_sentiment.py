"""
Sentiment analysis serverless function.

HTTP endpoint that:
1. Fetches unanalyzed announcements from database
2. Analyzes sentiment using Gemini
3. Updates announcements with sentiment results
4. Creates buy positions for POSITIVE sentiment (if buying enabled)

Can be called manually or triggered automatically after announcements are stored.
"""

from datetime import datetime
from typing import Dict, Any, List
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.db import (
    get_supabase_client,
    log_system_event,
    get_system_status,
    get_israel_time
)
from lib.gemini_client import analyze_announcement_sentiment, GeminiRateLimitError, GeminiAuthError
from lib.yfinance_client import get_current_price, get_price_with_fallback
from lib.trading_logic import should_buy


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_POST(self):
        """Handle POST request to analyze sentiments"""
        try:
            # Parse request body (optional parameters)
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                params = json.loads(body.decode('utf-8'))
            else:
                params = {}

            max_announcements = params.get('max_announcements', 10)

            result = analyze_pending_sentiments(max_announcements)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            log_system_event('ERROR', 'analyze_sentiment', f"Function failed: {e}", {})

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_GET(self):
        """Handle GET request (same as POST for convenience)"""
        self.do_POST()


def analyze_pending_sentiments(max_announcements: int = 10) -> Dict[str, Any]:
    """
    Analyze sentiment for pending announcements.

    Args:
        max_announcements: Maximum number of announcements to process

    Returns:
        Dict with execution summary
    """
    start_time = datetime.utcnow()

    log_system_event('INFO', 'analyze_sentiment', 'Starting sentiment analysis', {})

    # Check system status
    system_status = get_system_status()
    if system_status['status'] == 'DOWN':
        log_system_event(
            'WARNING',
            'analyze_sentiment',
            'System is DOWN, skipping sentiment analysis',
            {}
        )
        return {
            'success': False,
            'message': 'System is DOWN',
            'analyzed': 0,
            'positions_created': 0
        }

    # Fetch unanalyzed announcements
    client = get_supabase_client()

    result = client.table('announcements')\
        .select('*')\
        .eq('analyzed', False)\
        .order('published_at', desc=False)\
        .limit(max_announcements)\
        .execute()

    announcements = result.data

    if not announcements:
        log_system_event('INFO', 'analyze_sentiment', 'No pending announcements', {})
        return {
            'success': True,
            'message': 'No pending announcements',
            'analyzed': 0,
            'positions_created': 0
        }

    log_system_event(
        'INFO',
        'analyze_sentiment',
        f"Found {len(announcements)} pending announcements",
        {'count': len(announcements)}
    )

    # Process each announcement
    analyzed_count = 0
    positions_created = 0
    errors = []

    for announcement in announcements:
        try:
            # Analyze sentiment
            sentiment_result = analyze_announcement_sentiment(
                company_name=announcement['company_name'],
                ticker=announcement['ticker'],
                title=announcement['title'],
                content=announcement['content']
            )

            # Update announcement with sentiment
            client.table('announcements').update({
                'sentiment': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence'],
                'reasoning': sentiment_result['reasoning'],
                'analyzed': True
            }).eq('id', announcement['id']).execute()

            analyzed_count += 1

            log_system_event(
                'INFO',
                'analyze_sentiment',
                f"Analyzed announcement {announcement['announcement_id']}: {sentiment_result['sentiment']} ({sentiment_result['confidence']:.2f})",
                {
                    'announcement_id': announcement['announcement_id'],
                    'ticker': announcement['ticker'],
                    'sentiment': sentiment_result['sentiment'],
                    'confidence': sentiment_result['confidence']
                }
            )

            # Check if we should create a position
            if system_status['buying_enabled']:
                should_enter, position_size, reason = should_buy(
                    sentiment=sentiment_result['sentiment'],
                    confidence=sentiment_result['confidence'],
                    current_price=0.0,  # Dummy - will fetch below
                    daily_volume_ils=None
                )

                if should_enter:
                    # Fetch current price
                    try:
                        current_price = get_price_with_fallback(
                            announcement['ticker'],
                            fallback_price=None
                        )

                        # Create position
                        position_data = {
                            'ticker': announcement['ticker'],
                            'company_name': announcement['company_name'],
                            'announcement_id': announcement['announcement_id'],
                            'entry_price': current_price,
                            'peak_price': current_price,
                            'position_size_ils': position_size,
                            'entry_time': get_israel_time().isoformat(),
                            'sentiment': sentiment_result['sentiment'],
                            'confidence': sentiment_result['confidence'],
                            'reasoning': sentiment_result['reasoning'],
                            'entry_reason': reason
                        }

                        client.table('positions').insert(position_data).execute()
                        positions_created += 1

                        log_system_event(
                            'INFO',
                            'analyze_sentiment',
                            f"Created position for {announcement['ticker']}: ₪{position_size:.2f} @ {current_price:.2f}",
                            {
                                'ticker': announcement['ticker'],
                                'position_size': position_size,
                                'entry_price': current_price
                            }
                        )

                    except Exception as e:
                        log_system_event(
                            'ERROR',
                            'analyze_sentiment',
                            f"Failed to create position for {announcement['ticker']}: {e}",
                            {'announcement_id': announcement['announcement_id']}
                        )
                        errors.append(f"Position creation failed for {announcement['ticker']}: {e}")

        except (GeminiRateLimitError, GeminiAuthError) as e:
            # These are critical - stop processing
            log_system_event(
                'ERROR',
                'analyze_sentiment',
                f"Gemini API error: {e}",
                {'announcement_id': announcement.get('announcement_id')}
            )
            errors.append(f"Gemini API error: {e}")
            break

        except Exception as e:
            # Log but continue with other announcements
            log_system_event(
                'ERROR',
                'analyze_sentiment',
                f"Failed to analyze announcement {announcement.get('announcement_id')}: {e}",
                {'announcement': announcement}
            )
            errors.append(f"Failed to analyze {announcement.get('announcement_id')}: {e}")

    # Summary
    execution_time = (datetime.utcnow() - start_time).total_seconds()

    log_system_event(
        'INFO',
        'analyze_sentiment',
        f"Completed: {analyzed_count} analyzed, {positions_created} positions created",
        {
            'analyzed': analyzed_count,
            'positions_created': positions_created,
            'errors': len(errors),
            'execution_time_seconds': execution_time
        }
    )

    return {
        'success': True,
        'message': f'Analyzed {analyzed_count} announcements, created {positions_created} positions',
        'analyzed': analyzed_count,
        'positions_created': positions_created,
        'errors': errors,
        'execution_time_seconds': execution_time
    }
