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
import json
import logging
import time
import sys
import os
import requests

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

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuration constants
SLOW_GEMINI_RESPONSE_THRESHOLD_MS = 5000  # Warn if Gemini takes >5s (typical response is 1-3s)


def should_create_position() -> bool:
    """
    Check if automatic position creation is enabled.
    Reads from environment variable, defaults to True.
    """
    return os.getenv('AUTO_CREATE_POSITIONS', 'true').lower() == 'true'


def create_trading_position(announcement: Dict[str, Any], sentiment_result: Dict[str, Any]) -> None:
    """
    Create a trading position for a positive sentiment announcement.

    Args:
        announcement: Announcement data from database
        sentiment_result: Sentiment analysis result from Gemini
    """
    client = get_supabase_client()

    try:
        # Fetch current price
        current_price = get_price_with_fallback(
            announcement['ticker'],
            fallback_price=None
        )

        # Default to 100 shares (TODO: calculate based on position_size_ils / entry_price)
        # Create position matching database schema (announcement_id, ticker, entry_price, entry_time, quantity, status)
        position_data = {
            'announcement_id': announcement['id'],  # UUID
            'ticker': announcement['ticker'],
            'entry_price': current_price,
            'entry_time': get_israel_time().isoformat(),
            'quantity': 100,  # Default quantity
            'status': 'open'
        }

        client.table('positions').insert(position_data).execute()

        logger.info(
            f"[GEMINI] Created position for {announcement['ticker']}: "
            f"{position_data['quantity']} shares @ {current_price:.2f}"
        )

    except Exception as e:
        logger.error(
            f"[GEMINI] Failed to create position for {announcement['ticker']}: {e}"
        )


def analyze_single_announcement(announcement_id: str) -> Dict[str, Any]:
    """
    Analyze a single announcement by ID (called by database trigger).

    Returns:
        {
            'success': bool,
            'announcement_id': str,
            'sentiment': str,
            'processing_time_ms': int,
            'error': str (if failed),
            'skipped': bool (if already analyzed)
        }
    """
    start_time = time.time()
    logger.info(f"[GEMINI] Starting analysis for announcement: {announcement_id}")

    try:
        # Fetch the announcement
        logger.info(f"[GEMINI] Fetching announcement data: {announcement_id}")
        client = get_supabase_client()
        result = client.table('announcements')\
            .select('*')\
            .eq('id', announcement_id)\
            .single()\
            .execute()

        announcement = result.data

        # Skip if already analyzed
        if announcement.get('analyzed', False):
            logger.info(f"[GEMINI] Already analyzed, skipping: {announcement_id}")
            return {
                'success': True,
                'message': 'Already analyzed',
                'skipped': True,
                'announcement_id': announcement_id
            }

        # Call Gemini with timeout tracking
        logger.info(f"[GEMINI] Calling Gemini API for: {announcement['company_name']}")
        gemini_start = time.time()

        sentiment_result = analyze_announcement_sentiment(
            company_name=announcement['company_name'],
            ticker=announcement['ticker'],
            title=announcement['title'],
            content=announcement['content']
        )

        gemini_duration = (time.time() - gemini_start) * 1000
        logger.info(f"[GEMINI] API response received in {gemini_duration:.0f}ms")

        # Log if Gemini was slow
        if gemini_duration > SLOW_GEMINI_RESPONSE_THRESHOLD_MS:
            logger.warning(f"[GEMINI] SLOW RESPONSE: {gemini_duration:.0f}ms for {announcement_id}")

        # Update announcements table
        logger.info(f"[GEMINI] Updating database with sentiment: {sentiment_result['sentiment']}")
        client.table('announcements').update({
            'sentiment': sentiment_result['sentiment'],
            'confidence': None,
            'reasoning': sentiment_result['reasoning'],
            'analyzed': True
        }).eq('id', announcement_id).execute()

        # Insert into gemini_analyses audit table
        processing_time_ms = int((time.time() - start_time) * 1000)
        client.table('gemini_analyses').insert({
            'announcement_id': announcement_id,
            'sentiment': sentiment_result['sentiment'],
            'reasoning': sentiment_result['reasoning'],
            'confidence': None,
            'raw_response': sentiment_result['raw_response'],
            'processing_time_ms': processing_time_ms
        }).execute()

        logger.info(f"[GEMINI] Inserted audit record into gemini_analyses")

        # Optionally create trading position (if flag enabled)
        if should_create_position() and sentiment_result['sentiment'] == 'positive':
            logger.info(f"[GEMINI] Creating trading position (auto-create enabled)")
            create_trading_position(announcement, sentiment_result)
        elif sentiment_result['sentiment'] != 'positive':
            logger.info(f"[GEMINI] Skipping position creation (sentiment: {sentiment_result['sentiment']})")
        else:
            logger.info(f"[GEMINI] Skipping position creation (auto-create disabled)")

        total_duration = (time.time() - start_time) * 1000
        logger.info(f"[GEMINI] ✓ Complete in {total_duration:.0f}ms - Sentiment: {sentiment_result['sentiment']}")

        return {
            'success': True,
            'announcement_id': announcement_id,
            'sentiment': sentiment_result['sentiment'],
            'processing_time_ms': int(total_duration)
        }

    except TimeoutError as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"[GEMINI] ✗ TIMEOUT after {duration:.0f}ms for {announcement_id}: {str(e)}")

        # Log to gemini_errors table
        try:
            client.table('gemini_errors').insert({
                'announcement_id': announcement_id,
                'error_type': 'timeout',
                'error_message': str(e),
                'processing_time_ms': int(duration)
            }).execute()
        except Exception:
            pass

        return {
            'success': False,
            'error': 'timeout',
            'error_message': str(e),
            'announcement_id': announcement_id
        }

    except (GeminiAuthError, GeminiRateLimitError) as e:
        error_type = 'auth_error' if isinstance(e, GeminiAuthError) else 'rate_limit'
        duration = (time.time() - start_time) * 1000
        logger.error(f"[GEMINI] ✗ {error_type.upper()} after {duration:.0f}ms for {announcement_id}: {str(e)}")

        try:
            client.table('gemini_errors').insert({
                'announcement_id': announcement_id,
                'error_type': error_type,
                'error_message': str(e),
                'processing_time_ms': int(duration)
            }).execute()
        except Exception:
            pass

        return {
            'success': False,
            'error': error_type,
            'error_message': str(e),
            'announcement_id': announcement_id
        }

    except requests.exceptions.Timeout as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"[GEMINI] ✗ NETWORK TIMEOUT after {duration:.0f}ms for {announcement_id}")

        try:
            client.table('gemini_errors').insert({
                'announcement_id': announcement_id,
                'error_type': 'network_timeout',
                'error_message': str(e),
                'processing_time_ms': int(duration)
            }).execute()
        except Exception:
            pass

        return {
            'success': False,
            'error': 'network_timeout',
            'error_message': str(e),
            'announcement_id': announcement_id
        }

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"[GEMINI] ✗ INVALID JSON RESPONSE for {announcement_id}: {str(e)}")

        try:
            client.table('gemini_errors').insert({
                'announcement_id': announcement_id,
                'error_type': 'invalid_json',
                'error_message': str(e),
                'processing_time_ms': int((time.time() - start_time) * 1000)
            }).execute()
        except Exception:
            pass

        return {
            'success': False,
            'error': 'invalid_json',
            'error_message': str(e),
            'announcement_id': announcement_id
        }

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"[GEMINI] ✗ ERROR after {duration:.0f}ms for {announcement_id}: {str(e)}", exc_info=True)

        try:
            client.table('gemini_errors').insert({
                'announcement_id': announcement_id,
                'error_type': 'unknown',
                'error_message': str(e),
                'processing_time_ms': int(duration)
            }).execute()
        except Exception:
            pass

        return {
            'success': False,
            'error': 'unknown',
            'error_message': str(e),
            'announcement_id': announcement_id
        }


def handler(request):
    """
    Vercel serverless function handler.

    Supports two modes:
    1. POST with announcement_id - Single announcement (database trigger)
    2. GET with no params - Batch processing (existing cron, backwards compatible)
    """
    if request.method == 'POST':
        # Single announcement mode (database trigger)
        data = request.get_json()
        announcement_id = data.get('announcement_id')

        if not announcement_id:
            return {'error': 'announcement_id required'}, 400

        result = analyze_single_announcement(announcement_id)
        return result, 200 if result['success'] else 500

    else:
        # Batch mode (existing cron) - keep for backwards compatibility
        result = analyze_pending_sentiments(max_announcements=10)
        return result, 200


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
