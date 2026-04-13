"""Tests for TASE market calendar"""

import pytest
from datetime import datetime, time
import pytz
from src.shared.market_calendar import is_market_open


IL_TZ = pytz.timezone('Asia/Jerusalem')


def test_sunday_before_open():
    """Sunday 09:58 IL - market closed"""
    dt = IL_TZ.localize(datetime(2026, 4, 19, 9, 58))  # Sunday
    assert is_market_open(dt) is False


def test_sunday_opening():
    """Sunday 09:59 IL - market open"""
    dt = IL_TZ.localize(datetime(2026, 4, 19, 9, 59))  # Sunday
    assert is_market_open(dt) is True


def test_thursday_closing():
    """Thursday 17:15 IL - market still open"""
    dt = IL_TZ.localize(datetime(2026, 4, 23, 17, 15))  # Thursday
    assert is_market_open(dt) is True


def test_thursday_after_close():
    """Thursday 17:16 IL - market closed"""
    dt = IL_TZ.localize(datetime(2026, 4, 23, 17, 16))  # Thursday
    assert is_market_open(dt) is False


def test_friday_before_close():
    """Friday 13:35 IL - market still open"""
    dt = IL_TZ.localize(datetime(2026, 4, 24, 13, 35))  # Friday
    assert is_market_open(dt) is True


def test_friday_after_close():
    """Friday 13:36 IL - market closed"""
    dt = IL_TZ.localize(datetime(2026, 4, 24, 13, 36))  # Friday
    assert is_market_open(dt) is False


def test_saturday_always_closed():
    """Saturday any time - market closed"""
    dt = IL_TZ.localize(datetime(2026, 4, 25, 12, 0))  # Saturday
    assert is_market_open(dt) is False


def test_default_uses_current_time():
    """Calling without argument uses current time"""
    result = is_market_open()
    assert isinstance(result, bool)
