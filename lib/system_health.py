"""
System health monitoring for TASE trading system.

Monitors external service health and auto-pauses buying when systems become unstable.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from lib.db import get_supabase_client, log_system_event, update_system_status, get_israel_time
from lib.gemini_client import analyze_announcement_sentiment, GeminiRateLimitError, GeminiAuthError
from lib.yfinance_client import get_current_price, PriceFetchError
from lib.tase_scraper import fetch_announcements, ScraperError


# Health check thresholds
MAX_CONSECUTIVE_FAILURES = 3
HEALTH_CHECK_COOLDOWN_MINUTES = 5


class HealthCheckResult:
    """Result of a health check"""
    def __init__(self, service: str, healthy: bool, error: Optional[str] = None):
        self.service = service
        self.healthy = healthy
        self.error = error
        self.timestamp = get_israel_time()


def check_gemini_health() -> HealthCheckResult:
    """
    Check if Gemini API is responding.

    Returns:
        HealthCheckResult with service health status
    """
    try:
        # Quick test with minimal input
        result = analyze_announcement_sentiment(
            company_name="Test Company",
            ticker="TEST.TA",
            title="Test announcement",
            content="This is a test.",
            max_retries=1
        )

        # Validate response structure
        if not all(k in result for k in ['sentiment', 'confidence', 'reasoning']):
            return HealthCheckResult('gemini', False, "Invalid response structure")

        return HealthCheckResult('gemini', True)

    except GeminiRateLimitError as e:
        return HealthCheckResult('gemini', False, f"Rate limit: {e}")
    except GeminiAuthError as e:
        return HealthCheckResult('gemini', False, f"Auth error: {e}")
    except Exception as e:
        return HealthCheckResult('gemini', False, str(e))


def check_yfinance_health() -> HealthCheckResult:
    """
    Check if Yahoo Finance is responding.

    Returns:
        HealthCheckResult with service health status
    """
    try:
        # Test with a known ticker (Tower Semiconductor)
        price = get_current_price('TSEM.TA', use_cache=False)

        if price <= 0:
            return HealthCheckResult('yfinance', False, "Invalid price returned")

        return HealthCheckResult('yfinance', True)

    except PriceFetchError as e:
        return HealthCheckResult('yfinance', False, str(e))
    except Exception as e:
        return HealthCheckResult('yfinance', False, str(e))


def check_tase_scraper_health() -> HealthCheckResult:
    """
    Check if TASE scraper is working.

    Returns:
        HealthCheckResult with service health status
    """
    try:
        announcements = fetch_announcements(max_results=1)

        if not announcements:
            return HealthCheckResult('tase_scraper', False, "No announcements fetched")

        # Validate announcement structure
        required_fields = ['announcement_id', 'company_name', 'title', 'content', 'published_at']
        if not all(f in announcements[0] for f in required_fields):
            return HealthCheckResult('tase_scraper', False, "Invalid announcement structure")

        return HealthCheckResult('tase_scraper', True)

    except ScraperError as e:
        return HealthCheckResult('tase_scraper', False, str(e))
    except Exception as e:
        return HealthCheckResult('tase_scraper', False, str(e))


def check_database_health() -> HealthCheckResult:
    """
    Check if Supabase database is responding.

    Returns:
        HealthCheckResult with service health status
    """
    try:
        client = get_supabase_client()

        # Simple query to verify connection
        result = client.table('system_status').select('id').limit(1).execute()

        if not hasattr(result, 'data'):
            return HealthCheckResult('database', False, "Invalid response from database")

        return HealthCheckResult('database', True)

    except Exception as e:
        return HealthCheckResult('database', False, str(e))


def run_full_health_check() -> Dict[str, Any]:
    """
    Run health checks on all services.

    Returns:
        Dict with keys:
        - overall_healthy: bool
        - services: dict of service -> HealthCheckResult
        - unhealthy_services: list of service names
        - timestamp: datetime
    """
    checks = {
        'database': check_database_health(),
        'gemini': check_gemini_health(),
        'yfinance': check_yfinance_health(),
        'tase_scraper': check_tase_scraper_health()
    }

    unhealthy = [name for name, result in checks.items() if not result.healthy]
    overall_healthy = len(unhealthy) == 0

    return {
        'overall_healthy': overall_healthy,
        'services': checks,
        'unhealthy_services': unhealthy,
        'timestamp': get_israel_time()
    }


def update_system_health_status(health_result: Dict[str, Any]) -> None:
    """
    Update system status based on health check results.

    Auto-pauses buying if critical services are unhealthy.

    Args:
        health_result: Result from run_full_health_check()
    """
    try:
        unhealthy = health_result['unhealthy_services']

        # Determine system status
        if not unhealthy:
            status = 'HEALTHY'
            buying_enabled = True
        elif 'database' in unhealthy:
            # Database down = full system down
            status = 'DOWN'
            buying_enabled = False
        else:
            # Some services down = degraded
            status = 'DEGRADED'
            # Disable buying if Gemini or TASE scraper are down (critical for new positions)
            buying_enabled = 'gemini' not in unhealthy and 'tase_scraper' not in unhealthy

        # Update database
        update_system_status({
            'status': status,
            'buying_enabled': buying_enabled,
            'last_check': health_result['timestamp'].isoformat(),
            'metadata': {
                'unhealthy_services': unhealthy,
                'service_details': {
                    name: {
                        'healthy': result.healthy,
                        'error': result.error
                    }
                    for name, result in health_result['services'].items()
                }
            }
        })

        # Log status change
        if unhealthy:
            log_system_event(
                'WARNING',
                'system_health',
                f"System status: {status}. Unhealthy services: {', '.join(unhealthy)}",
                {'unhealthy_services': unhealthy, 'buying_enabled': buying_enabled}
            )
        else:
            log_system_event(
                'INFO',
                'system_health',
                "All systems healthy",
                {'status': status}
            )

    except Exception as e:
        # Log error but don't raise (health checks shouldn't crash the app)
        print(f"Failed to update system health status: {e}")
        log_system_event(
            'ERROR',
            'system_health',
            f"Failed to update health status: {e}",
            {}
        )


def should_run_health_check() -> bool:
    """
    Determine if health check should run based on cooldown period.

    Returns:
        bool: True if health check should run, False if in cooldown
    """
    try:
        client = get_supabase_client()
        result = client.table('system_status').select('last_check').single().execute()

        if not result.data or not result.data.get('last_check'):
            return True

        last_check = datetime.fromisoformat(result.data['last_check'])
        now = get_israel_time()

        # Remove timezone info for comparison if needed
        if last_check.tzinfo:
            time_since_check = now - last_check
        else:
            time_since_check = now.replace(tzinfo=None) - last_check

        return time_since_check >= timedelta(minutes=HEALTH_CHECK_COOLDOWN_MINUTES)

    except Exception as e:
        # If we can't check, assume we should run
        print(f"Error checking health check cooldown: {e}")
        return True
