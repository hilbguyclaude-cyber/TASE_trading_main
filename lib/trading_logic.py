"""
Trading logic for TASE trading system.

Implements buy/sell decision rules based on sentiment analysis:
- BUY: POSITIVE sentiment with confidence >= 0.7
- SELL: 60 minutes after entry OR -1% drop from peak_price
- Position sizing: MIN(1% of daily volume ₪, ₪5,000 max)
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import pytz
from lib.db import get_supabase_client, get_israel_time


# Trading parameters
SENTIMENT_THRESHOLD = 0.7  # Minimum confidence for buy signal
POSITION_HOLD_MINUTES = 60  # Minutes to hold position before selling
STOP_LOSS_PERCENT = 0.01  # -1% drop from peak triggers sell
MAX_POSITION_SIZE_ILS = 5000  # Maximum position size in ILS
DAILY_VOLUME_PERCENT = 0.01  # 1% of daily volume


class InsufficientDataError(Exception):
    """Raised when required data is unavailable"""
    pass


def should_buy(
    sentiment: str,
    confidence: float,
    current_price: float,
    daily_volume_ils: Optional[float] = None
) -> Tuple[bool, Optional[float], str]:
    """
    Determine if we should buy based on sentiment analysis.

    Args:
        sentiment: Sentiment value (POSITIVE, NEGATIVE, NEUTRAL)
        confidence: Confidence score (0.0-1.0)
        current_price: Current stock price
        daily_volume_ils: Optional daily trading volume in ILS

    Returns:
        Tuple of (should_buy: bool, position_size_ils: float|None, reason: str)

    Raises:
        InsufficientDataError: If required data is missing
    """
    # Validate inputs
    if not sentiment:
        raise InsufficientDataError("Sentiment is required")

    if current_price <= 0:
        raise InsufficientDataError("Valid current price is required")

    # Check sentiment and confidence threshold
    if sentiment != 'POSITIVE':
        return False, None, f"Sentiment is {sentiment}, not POSITIVE"

    if confidence < SENTIMENT_THRESHOLD:
        return False, None, f"Confidence {confidence:.2f} below threshold {SENTIMENT_THRESHOLD}"

    # Calculate position size
    position_size = calculate_position_size(current_price, daily_volume_ils)

    return True, position_size, f"POSITIVE sentiment with {confidence:.2f} confidence"


def should_sell(
    entry_time: datetime,
    entry_price: float,
    peak_price: float,
    current_price: float,
    current_time: Optional[datetime] = None
) -> Tuple[bool, str]:
    """
    Determine if we should sell an existing position.

    Sell triggers:
    1. 60 minutes have passed since entry
    2. Price dropped 1% or more from peak_price

    Args:
        entry_time: When position was entered
        entry_price: Price at entry
        peak_price: Highest price seen since entry
        current_price: Current stock price
        current_time: Current time (defaults to now in Israel timezone)

    Returns:
        Tuple of (should_sell: bool, reason: str)

    Raises:
        InsufficientDataError: If required data is missing or invalid
    """
    # Validate inputs
    if entry_price <= 0 or peak_price <= 0 or current_price <= 0:
        raise InsufficientDataError("All prices must be positive")

    if peak_price < entry_price:
        raise InsufficientDataError("Peak price cannot be less than entry price")

    if current_time is None:
        current_time = get_israel_time()

    # Check time-based exit (60 minutes)
    time_held = current_time - entry_time
    if time_held >= timedelta(minutes=POSITION_HOLD_MINUTES):
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        return True, f"Time limit reached (60min), profit: {profit_pct:+.2f}%"

    # Check stop-loss from peak (-1%)
    drop_from_peak = (current_price - peak_price) / peak_price
    if drop_from_peak <= -STOP_LOSS_PERCENT:
        drop_pct = drop_from_peak * 100
        return True, f"Stop loss triggered: {drop_pct:.2f}% drop from peak"

    # No sell trigger
    return False, "Hold position"


def calculate_position_size(
    price: float,
    daily_volume_ils: Optional[float] = None
) -> float:
    """
    Calculate position size in ILS.

    Formula: MIN(1% of daily_volume_ils, ₪5,000)
    If daily_volume_ils unavailable, use maximum ₪5,000

    Args:
        price: Current stock price (not used in calculation but kept for future enhancements)
        daily_volume_ils: Daily trading volume in ILS

    Returns:
        float: Position size in ILS
    """
    if daily_volume_ils and daily_volume_ils > 0:
        volume_based = daily_volume_ils * DAILY_VOLUME_PERCENT
        return min(volume_based, MAX_POSITION_SIZE_ILS)

    # No volume data - use maximum
    return MAX_POSITION_SIZE_ILS


def update_peak_price(position_id: str, new_peak: float) -> None:
    """
    Update peak_price for a position in the database.

    Args:
        position_id: Position UUID
        new_peak: New peak price to set

    Raises:
        Exception: Re-raises database errors after logging
    """
    try:
        client = get_supabase_client()

        client.table('positions')\
            .update({'peak_price': new_peak})\
            .eq('id', position_id)\
            .execute()

    except Exception as e:
        print(f"Failed to update peak price for position {position_id}: {e}")
        raise


def close_position(
    position_id: str,
    exit_price: float,
    exit_reason: str
) -> Dict[str, Any]:
    """
    Close a position in the database.

    Updates:
    - exit_price
    - exit_time (current Israel time)
    - profit_loss_ils (calculated)
    - profit_loss_percent (calculated)
    - exit_reason

    Args:
        position_id: Position UUID
        exit_price: Price at exit
        exit_reason: Reason for closing position

    Returns:
        Dict: Updated position record

    Raises:
        Exception: Re-raises database errors after logging
    """
    try:
        client = get_supabase_client()

        # Get current position to calculate P&L
        result = client.table('positions')\
            .select('*')\
            .eq('id', position_id)\
            .single()\
            .execute()

        position = result.data

        # Calculate profit/loss
        entry_price = float(position['entry_price'])
        position_size = float(position['position_size_ils'])

        profit_loss_percent = ((exit_price - entry_price) / entry_price) * 100
        profit_loss_ils = position_size * (profit_loss_percent / 100)

        # Update position
        update_result = client.table('positions')\
            .update({
                'exit_price': exit_price,
                'exit_time': get_israel_time().isoformat(),
                'profit_loss_ils': profit_loss_ils,
                'profit_loss_percent': profit_loss_percent,
                'exit_reason': exit_reason
            })\
            .eq('id', position_id)\
            .execute()

        if not update_result.data:
            raise Exception("Failed to update position")

        return update_result.data[0]

    except Exception as e:
        print(f"Failed to close position {position_id}: {e}")
        raise


def get_open_positions() -> list[Dict[str, Any]]:
    """
    Fetch all open positions from database.

    Returns:
        List of position dicts with exit_time = NULL

    Raises:
        Exception: Re-raises database errors after logging
    """
    try:
        client = get_supabase_client()

        result = client.table('positions')\
            .select('*')\
            .is_('exit_time', 'null')\
            .execute()

        return result.data

    except Exception as e:
        print(f"Failed to fetch open positions: {e}")
        raise
