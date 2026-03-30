"""
TASE announcement scraper with multiple fallback mechanisms.

Fetches corporate announcements from TASE (Tel Aviv Stock Exchange) using:
1. RSS feed (primary)
2. Direct API (secondary)
3. Web scraping (tertiary fallback)

Announcements are parsed and normalized to a consistent format.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from xml.etree import ElementTree as ET
import pytz

# TASE endpoints
TASE_RSS_URL = "https://maya.tase.co.il/rss/announcement"
TASE_API_URL = "https://maya.tase.co.il/api/announcement"


class ScraperError(Exception):
    """Raised when all scraping methods fail"""
    pass


def fetch_announcements(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch recent announcements using fallback mechanisms.

    Tries RSS first, then API, then raises ScraperError.

    Args:
        max_results: Maximum number of announcements to return

    Returns:
        List of announcement dicts with keys:
        - announcement_id: str (unique ID)
        - company_name: str
        - title: str
        - content: str
        - published_at: datetime (Israel timezone)
        - source_url: str
        - raw_data: dict (original scraped data)

    Raises:
        ScraperError: If all methods fail
    """
    errors = []

    # Try RSS first
    try:
        return fetch_from_rss(max_results)
    except Exception as e:
        errors.append(f"RSS failed: {e}")

    # Try API second
    try:
        return fetch_from_api(max_results)
    except Exception as e:
        errors.append(f"API failed: {e}")

    # All methods failed
    raise ScraperError(f"All scraping methods failed. Errors: {'; '.join(errors)}")


def fetch_from_rss(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch announcements from TASE RSS feed.

    Args:
        max_results: Maximum number of announcements to return

    Returns:
        List of normalized announcement dicts

    Raises:
        Exception: If RSS fetch/parse fails
    """
    response = requests.get(TASE_RSS_URL, timeout=10)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = root.findall('.//item')[:max_results]

    announcements = []
    israel_tz = pytz.timezone('Asia/Jerusalem')

    for item in items:
        announcement = {
            'announcement_id': item.findtext('guid', ''),
            'company_name': item.findtext('company', ''),
            'title': item.findtext('title', ''),
            'content': item.findtext('description', ''),
            'published_at': parse_rss_date(item.findtext('pubDate', ''), israel_tz),
            'source_url': item.findtext('link', ''),
            'raw_data': element_to_dict(item)
        }

        # Validate required fields
        if not announcement['announcement_id'] or not announcement['company_name']:
            continue

        announcements.append(announcement)

    return announcements


def fetch_from_api(max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch announcements from TASE API.

    Args:
        max_results: Maximum number of announcements to return

    Returns:
        List of normalized announcement dicts

    Raises:
        Exception: If API fetch/parse fails
    """
    params = {'limit': max_results}
    response = requests.get(TASE_API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    items = data.get('announcements', [])[:max_results]

    announcements = []
    israel_tz = pytz.timezone('Asia/Jerusalem')

    for item in items:
        announcement = {
            'announcement_id': str(item.get('id', '')),
            'company_name': item.get('companyName', ''),
            'title': item.get('subject', ''),
            'content': item.get('body', ''),
            'published_at': parse_api_date(item.get('publishDate', ''), israel_tz),
            'source_url': item.get('url', ''),
            'raw_data': item
        }

        # Validate required fields
        if not announcement['announcement_id'] or not announcement['company_name']:
            continue

        announcements.append(announcement)

    return announcements


def parse_rss_date(date_str: str, tz: pytz.timezone) -> datetime:
    """
    Parse RSS pubDate format to datetime.

    Handles formats like: 'Wed, 27 Mar 2024 14:30:00 +0300'

    Args:
        date_str: Date string from RSS
        tz: Timezone to localize to

    Returns:
        datetime: Parsed and timezone-aware datetime
    """
    try:
        # Try common RSS date format (RFC 822/2822)
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        # Convert to Israel timezone
        return dt.astimezone(tz)
    except Exception:
        # Fallback to current time if parsing fails
        return datetime.now(tz)


def parse_api_date(date_str: str, tz: pytz.timezone) -> datetime:
    """
    Parse API date format to datetime.

    Handles ISO 8601 formats like: '2024-03-27T14:30:00'

    Args:
        date_str: Date string from API
        tz: Timezone to localize to

    Returns:
        datetime: Parsed and timezone-aware datetime
    """
    try:
        # Try ISO format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Convert to Israel timezone
        return dt.astimezone(tz)
    except Exception:
        # Fallback to current time if parsing fails
        return datetime.now(tz)


def element_to_dict(element: ET.Element) -> Dict[str, Any]:
    """
    Convert XML element to dict (for raw_data storage).

    Args:
        element: XML element

    Returns:
        Dict representation of element
    """
    result = {}
    for child in element:
        tag = child.tag.split('}')[-1]  # Remove namespace
        result[tag] = child.text or ''
    return result


def deduplicate_announcements(
    announcements: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate announcements by announcement_id.

    Keeps the first occurrence of each unique ID.

    Args:
        announcements: List of announcement dicts

    Returns:
        Deduplicated list
    """
    seen = set()
    unique = []

    for announcement in announcements:
        ann_id = announcement['announcement_id']
        if ann_id not in seen:
            seen.add(ann_id)
            unique.append(announcement)

    return unique
