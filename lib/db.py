"""
Database utilities for TASE Trading System.

Provides helper functions for Supabase database operations including:
- Supabase client connection
- System logging and status management
- Company/ticker lookups with fuzzy matching
- Trading hours checks (Israel timezone)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, time
import pytz
from supabase import create_client, Client

# Cache Supabase client to avoid repeated connections
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.

    Returns:
        Client: Authenticated Supabase client

    Raises:
        ValueError: If required environment variables are missing
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')

    if not url or not key:
        raise ValueError(
            "Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_KEY"
        )

    _supabase_client = create_client(url, key)
    return _supabase_client


def log_system_event(
    level: str,
    component: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a system event to the system_logs table.

    Args:
        level: Log level (INFO, WARNING, ERROR, CRITICAL)
        component: Component name (e.g., 'scraper', 'analyzer', 'trading_engine')
        message: Log message
        metadata: Optional metadata dictionary

    Raises:
        ValueError: If level is not one of the allowed values
    """
    # Validate log level
    allowed_levels = ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
    if level not in allowed_levels:
        raise ValueError(f"Invalid log level: {level}. Must be one of {allowed_levels}")

    try:
        client = get_supabase_client()

        log_entry = {
            'level': level,
            'component': component,
            'message': message,
            'metadata': metadata or {}
        }

        client.table('system_logs').insert(log_entry).execute()
    except Exception as e:
        # Don't raise - logging failures shouldn't crash the app
        print(f"Failed to log system event: {e}")


def get_system_status() -> Dict[str, Any]:
    """
    Fetch the current system status.

    Returns:
        Dict containing system status fields:
        - status: 'HEALTHY', 'DEGRADED', or 'DOWN'
        - buying_enabled: Boolean
        - selling_enabled: Boolean
        - last_check: Timestamp
        - metadata: Additional status data

    Raises:
        ValueError: If no system status record exists
    """
    client = get_supabase_client()

    result = client.table('system_status').select('*').execute()

    if not result.data:
        raise ValueError("No system status record found")

    return result.data[0]


def update_system_status(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the system status record.

    Args:
        updates: Dictionary of fields to update

    Returns:
        Dict: Updated system status record

    Raises:
        ValueError: If no system status record exists
    """
    client = get_supabase_client()

    # Get current status to find the ID
    current_status = get_system_status()

    # Update the record
    result = client.table('system_status')\
        .update(updates)\
        .eq('id', current_status['id'])\
        .execute()

    if not result.data:
        raise ValueError("Failed to update system status")

    return result.data[0]


def get_company_by_ticker(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Look up a company by its ticker symbol.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with company data if found, None otherwise
    """
    client = get_supabase_client()

    result = client.table('companies')\
        .select('*')\
        .eq('ticker', ticker.upper())\
        .execute()

    if result.data:
        return result.data[0]
    return None


def lookup_ticker_by_company_name(company_name: str) -> Optional[str]:
    """
    Look up a ticker symbol by company name using fuzzy matching.

    Uses PostgreSQL full-text search for flexible matching.

    Args:
        company_name: Company name to search for

    Returns:
        Ticker symbol if found, None otherwise
    """
    client = get_supabase_client()

    # First try exact match (case-insensitive)
    result = client.table('companies')\
        .select('ticker')\
        .ilike('company_name', company_name)\
        .execute()

    if result.data:
        return result.data[0]['ticker']

    # Try full-text search for fuzzy matching
    # Use plainto_tsquery for simple search
    result = client.rpc(
        'search_companies',
        {'search_query': company_name}
    ).execute()

    if result.data:
        return result.data[0]['ticker']

    return None


def insert_unmapped_company(
    company_name: str,
    source: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add a company to the unmapped companies queue for manual review.

    Args:
        company_name: Name of the company that couldn't be mapped
        source: Source where the company was found (e.g., 'maya', 'tase')
        metadata: Optional metadata about the company

    Raises:
        Exception: Re-raises any database errors after logging
    """
    try:
        client = get_supabase_client()

        entry = {
            'company_name': company_name,
            'source': source,
            'status': 'PENDING',
            'metadata': metadata or {}
        }

        client.table('unmapped_companies').insert(entry).execute()
    except Exception as e:
        print(f"Failed to insert unmapped company: {e}")
        raise  # Re-raise since this is not critical path


def get_israel_time() -> datetime:
    """
    Get current time in Israel timezone (Asia/Jerusalem).

    Returns:
        datetime: Current time in Israel timezone
    """
    israel_tz = pytz.timezone('Asia/Jerusalem')
    return datetime.now(israel_tz)


def is_during_trading_hours() -> bool:
    """
    Check if current time is during TASE trading hours.

    TASE trading hours (Israel time):
    - Sunday-Thursday: 09:59 - 17:25
    - Friday: 09:59 - 14:30 (shortened day)
    - Saturday: Closed

    Returns:
        bool: True if currently during trading hours, False otherwise
    """
    now = get_israel_time()

    # Python's isoweekday():
    # Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5, Saturday=6, Sunday=7
    weekday = now.isoweekday()

    # Saturday is closed
    if weekday == 6:
        return False

    current_time = now.time()
    trading_start = time(9, 59)

    # Friday has shortened hours (09:59 - 14:30)
    if weekday == 5:
        trading_end = time(14, 30)
        return trading_start <= current_time <= trading_end

    # Sunday-Thursday: normal hours (09:59 - 17:25)
    trading_end = time(17, 25)
    return trading_start <= current_time <= trading_end
