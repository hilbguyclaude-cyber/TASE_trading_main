import pytest
from datetime import datetime
import pytz
import requests
from unittest.mock import Mock, patch
from lib.tase_scraper import (
    fetch_announcements,
    fetch_from_rss,
    fetch_from_api,
    parse_rss_date,
    parse_api_date,
    element_to_dict,
    deduplicate_announcements,
    ScraperError
)


# Sample RSS XML response
SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <item>
            <guid>ANN001</guid>
            <company>Tower Semiconductor</company>
            <title>Quarterly Results</title>
            <description>Q1 2024 earnings report</description>
            <pubDate>Wed, 27 Mar 2024 14:30:00 +0300</pubDate>
            <link>https://maya.tase.co.il/ann/ANN001</link>
        </item>
        <item>
            <guid>ANN002</guid>
            <company>Teva Pharmaceutical</company>
            <title>Product Launch</title>
            <description>New drug approval</description>
            <pubDate>Thu, 28 Mar 2024 09:00:00 +0300</pubDate>
            <link>https://maya.tase.co.il/ann/ANN002</link>
        </item>
    </channel>
</rss>"""

# Sample API JSON response
SAMPLE_API = {
    "announcements": [
        {
            "id": "ANN003",
            "companyName": "ICL Group",
            "subject": "Dividend Declaration",
            "body": "Board approved dividend payment",
            "publishDate": "2024-03-29T10:15:00",
            "url": "https://maya.tase.co.il/ann/ANN003"
        },
        {
            "id": "ANN004",
            "companyName": "NICE Systems",
            "subject": "Partnership Agreement",
            "body": "Strategic partnership announced",
            "publishDate": "2024-03-30T13:45:00",
            "url": "https://maya.tase.co.il/ann/ANN004"
        }
    ]
}


def test_fetch_from_rss_success():
    """Test successful RSS feed fetch and parse"""
    with patch('lib.tase_scraper.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.content = SAMPLE_RSS.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        announcements = fetch_from_rss(max_results=10)

        assert len(announcements) == 2
        assert announcements[0]['announcement_id'] == 'ANN001'
        assert announcements[0]['company_name'] == 'Tower Semiconductor'
        assert announcements[0]['title'] == 'Quarterly Results'
        assert announcements[0]['content'] == 'Q1 2024 earnings report'
        assert announcements[1]['announcement_id'] == 'ANN002'


def test_fetch_from_rss_max_results():
    """Test RSS max_results limit"""
    with patch('lib.tase_scraper.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.content = SAMPLE_RSS.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        announcements = fetch_from_rss(max_results=1)

        assert len(announcements) == 1
        assert announcements[0]['announcement_id'] == 'ANN001'


def test_fetch_from_rss_network_error():
    """Test RSS fetch with network error"""
    with patch('lib.tase_scraper.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        with pytest.raises(Exception):
            fetch_from_rss()


def test_fetch_from_api_success():
    """Test successful API fetch and parse"""
    with patch('lib.tase_scraper.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_API
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        announcements = fetch_from_api(max_results=10)

        assert len(announcements) == 2
        assert announcements[0]['announcement_id'] == 'ANN003'
        assert announcements[0]['company_name'] == 'ICL Group'
        assert announcements[0]['title'] == 'Dividend Declaration'
        assert announcements[1]['announcement_id'] == 'ANN004'


def test_fetch_from_api_max_results():
    """Test API max_results limit"""
    with patch('lib.tase_scraper.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_API
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        announcements = fetch_from_api(max_results=1)

        assert len(announcements) == 1
        assert announcements[0]['announcement_id'] == 'ANN003'


def test_fetch_from_api_network_error():
    """Test API fetch with network error"""
    with patch('lib.tase_scraper.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(Exception):
            fetch_from_api()


def test_fetch_announcements_rss_success():
    """Test fetch_announcements with RSS success (primary method)"""
    with patch('lib.tase_scraper.fetch_from_rss') as mock_rss:
        mock_rss.return_value = [{'announcement_id': 'TEST001'}]

        announcements = fetch_announcements()

        assert len(announcements) == 1
        assert mock_rss.called


def test_fetch_announcements_fallback_to_api():
    """Test fetch_announcements falls back to API when RSS fails"""
    with patch('lib.tase_scraper.fetch_from_rss') as mock_rss, \
         patch('lib.tase_scraper.fetch_from_api') as mock_api:

        mock_rss.side_effect = Exception("RSS failed")
        mock_api.return_value = [{'announcement_id': 'TEST002'}]

        announcements = fetch_announcements()

        assert len(announcements) == 1
        assert announcements[0]['announcement_id'] == 'TEST002'
        assert mock_api.called


def test_fetch_announcements_all_methods_fail():
    """Test fetch_announcements raises ScraperError when all methods fail"""
    with patch('lib.tase_scraper.fetch_from_rss') as mock_rss, \
         patch('lib.tase_scraper.fetch_from_api') as mock_api:

        mock_rss.side_effect = Exception("RSS failed")
        mock_api.side_effect = Exception("API failed")

        with pytest.raises(ScraperError, match="All scraping methods failed"):
            fetch_announcements()


def test_parse_rss_date():
    """Test RSS date parsing"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    date_str = "Wed, 27 Mar 2024 14:30:00 +0300"

    dt = parse_rss_date(date_str, israel_tz)

    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_parse_rss_date_invalid():
    """Test RSS date parsing with invalid date (fallback to now)"""
    israel_tz = pytz.timezone('Asia/Jerusalem')

    dt = parse_rss_date("invalid date", israel_tz)

    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_parse_api_date():
    """Test API date parsing"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    date_str = "2024-03-29T10:15:00"

    dt = parse_api_date(date_str, israel_tz)

    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_parse_api_date_with_z():
    """Test API date parsing with Z suffix"""
    israel_tz = pytz.timezone('Asia/Jerusalem')
    date_str = "2024-03-29T10:15:00Z"

    dt = parse_api_date(date_str, israel_tz)

    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_parse_api_date_invalid():
    """Test API date parsing with invalid date (fallback to now)"""
    israel_tz = pytz.timezone('Asia/Jerusalem')

    dt = parse_api_date("not a date", israel_tz)

    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_element_to_dict():
    """Test XML element to dict conversion"""
    from xml.etree import ElementTree as ET

    xml = '<item><title>Test Title</title><description>Test Description</description></item>'
    element = ET.fromstring(xml)

    result = element_to_dict(element)

    assert result['title'] == 'Test Title'
    assert result['description'] == 'Test Description'


def test_deduplicate_announcements():
    """Test announcement deduplication"""
    announcements = [
        {'announcement_id': 'ANN001', 'title': 'First'},
        {'announcement_id': 'ANN002', 'title': 'Second'},
        {'announcement_id': 'ANN001', 'title': 'Duplicate'},
        {'announcement_id': 'ANN003', 'title': 'Third'},
    ]

    unique = deduplicate_announcements(announcements)

    assert len(unique) == 3
    assert unique[0]['announcement_id'] == 'ANN001'
    assert unique[0]['title'] == 'First'  # Keeps first occurrence
    assert unique[1]['announcement_id'] == 'ANN002'
    assert unique[2]['announcement_id'] == 'ANN003'


def test_deduplicate_announcements_empty():
    """Test deduplication with empty list"""
    unique = deduplicate_announcements([])
    assert len(unique) == 0
