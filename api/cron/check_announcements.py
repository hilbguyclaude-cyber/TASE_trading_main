"""
Announcement checker cron job.

Runs every minute (via Vercel cron) to:
1. Check system health
2. Fetch new announcements from TASE
3. Deduplicate and store in database
4. Trigger sentiment analysis for new announcements

Vercel serverless function handler.
"""

from datetime import datetime
from typing import Dict, Any
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add lib to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from lib.db import (
    get_supabase_client,
    log_system_event,
    get_system_status,
    is_during_trading_hours,
    lookup_ticker_by_company_name,
    insert_unmapped_company
)
from lib.tase_scraper import fetch_announcements, deduplicate_announcements
from lib.system_health import should_run_health_check, run_full_health_check, update_system_health_status


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_GET(self):
        """Handle GET request from Vercel cron"""
        try:
            result = check_announcements()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            log_system_event('ERROR', 'check_announcements_cron', f"Cron job failed: {e}", {})

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())


def check_announcements() -> Dict[str, Any]:
    """
    Main cron job logic for checking announcements.

    Returns:
        Dict with execution summary
    """
    start_time = datetime.utcnow()

    log_system_event('INFO', 'check_announcements_cron', 'Cron job started', {})

    # Step 1: Health check (if cooldown expired)
    if should_run_health_check():
        log_system_event('INFO', 'check_announcements_cron', 'Running health check', {})
        health_result = run_full_health_check()
        update_system_health_status(health_result)

    # Step 2: Check if during trading hours
    if not is_during_trading_hours():
        log_system_event(
            'INFO',
            'check_announcements_cron',
            'Outside trading hours, skipping announcement fetch',
            {}
        )
        return {
            'success': True,
            'message': 'Outside trading hours',
            'announcements_processed': 0
        }

    # Step 3: Check system status
    system_status = get_system_status()
    if system_status['status'] == 'DOWN':
        log_system_event(
            'WARNING',
            'check_announcements_cron',
            'System is DOWN, skipping announcement fetch',
            {}
        )
        return {
            'success': False,
            'message': 'System is DOWN',
            'announcements_processed': 0
        }

    # Step 4: Fetch announcements
    try:
        announcements = fetch_announcements(max_results=50)
        announcements = deduplicate_announcements(announcements)

        log_system_event(
            'INFO',
            'check_announcements_cron',
            f"Fetched {len(announcements)} announcements",
            {'count': len(announcements)}
        )
    except Exception as e:
        log_system_event(
            'ERROR',
            'check_announcements_cron',
            f"Failed to fetch announcements: {e}",
            {}
        )
        return {
            'success': False,
            'message': f'Failed to fetch announcements: {e}',
            'announcements_processed': 0
        }

    # Step 5: Process and store announcements
    processed_count = 0
    new_count = 0
    unmapped_companies = []

    client = get_supabase_client()

    for announcement in announcements:
        try:
            # Check if already exists
            existing = client.table('announcements')\
                .select('id')\
                .eq('announcement_id', announcement['announcement_id'])\
                .execute()

            if existing.data:
                # Already processed
                continue

            # Look up ticker
            ticker = lookup_ticker_by_company_name(announcement['company_name'])

            if not ticker:
                # Company not mapped - queue for manual review
                if announcement['company_name'] not in unmapped_companies:
                    unmapped_companies.append(announcement['company_name'])
                    insert_unmapped_company(
                        announcement['company_name'],
                        'tase',
                        {'announcement_id': announcement['announcement_id']}
                    )
                continue

            # Insert announcement (sentiment will be filled by analyze_sentiment function)
            client.table('announcements').insert({
                'announcement_id': announcement['announcement_id'],
                'company_name': announcement['company_name'],
                'ticker': ticker,
                'title': announcement['title'],
                'content': announcement['content'],
                'published_at': announcement['published_at'].isoformat(),
                'source_url': announcement['source_url'],
                'raw_data': announcement['raw_data'],
                'sentiment': None,  # Will be filled by sentiment analysis
                'confidence': None,
                'reasoning': None,
                'analyzed': False
            }).execute()

            new_count += 1
            processed_count += 1

        except Exception as e:
            log_system_event(
                'ERROR',
                'check_announcements_cron',
                f"Failed to process announcement {announcement.get('announcement_id')}: {e}",
                {'announcement': announcement}
            )

    # Log summary
    execution_time = (datetime.utcnow() - start_time).total_seconds()

    log_system_event(
        'INFO',
        'check_announcements_cron',
        f"Completed: {new_count} new announcements stored",
        {
            'total_fetched': len(announcements),
            'new_stored': new_count,
            'already_processed': len(announcements) - processed_count,
            'unmapped_companies': unmapped_companies,
            'execution_time_seconds': execution_time
        }
    )

    return {
        'success': True,
        'message': f'Processed {new_count} new announcements',
        'announcements_fetched': len(announcements),
        'announcements_processed': new_count,
        'unmapped_companies': unmapped_companies,
        'execution_time_seconds': execution_time
    }
