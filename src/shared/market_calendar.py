"""TASE Market Calendar - Single Source of Truth for Trading Hours"""

from datetime import datetime, time
from typing import Optional
import pytz
import holidays

# Israeli timezone
IL_TZ = pytz.timezone('Asia/Jerusalem')

# TASE trading hours
SUNDAY_TO_THURSDAY_OPEN = time(9, 59)
SUNDAY_TO_THURSDAY_CLOSE = time(17, 15)
FRIDAY_OPEN = time(9, 59)
FRIDAY_CLOSE = time(13, 35)

# Israeli holidays
il_holidays = holidays.Israel(years=range(2026, 2030))


def is_market_open(check_time: Optional[datetime] = None) -> bool:
    """
    Check if TASE market is currently open

    Trading hours:
    - Sunday-Thursday: 09:59 - 17:15 IL time
    - Friday: 09:59 - 13:35 IL time
    - Saturday: Closed
    - Israeli holidays: Closed

    Args:
        check_time: Optional datetime to check (defaults to now).
                   If naive, assumed to be IL time. If aware, converted to IL time.

    Returns:
        True if market is open, False otherwise
    """
    if check_time is None:
        check_time = datetime.now(IL_TZ)
    elif check_time.tzinfo is None:
        # Naive datetime - assume IL time
        check_time = IL_TZ.localize(check_time)
    else:
        # Convert to IL time
        check_time = check_time.astimezone(IL_TZ)

    # Saturday always closed
    if check_time.weekday() == 5:  # 5 = Saturday
        return False

    # Israeli holidays closed
    if check_time.date() in il_holidays:
        return False

    current_time = check_time.time()

    # Friday (weekday 4)
    if check_time.weekday() == 4:
        return FRIDAY_OPEN <= current_time <= FRIDAY_CLOSE

    # Sunday-Thursday (weekday 6, 0-3)
    return SUNDAY_TO_THURSDAY_OPEN <= current_time <= SUNDAY_TO_THURSDAY_CLOSE
