"""
Gemini API client for sentiment analysis.

Provides integration with Google's Gemini 1.5 Flash model to analyze
TASE announcements and determine trading sentiment with confidence scores.
"""

import os
import json
import time
from typing import Dict, Any
import google.generativeai as genai
from lib.db import log_system_event


# Custom exceptions
class GeminiRateLimitError(Exception):
    """Raised when Gemini API rate limit is exceeded."""
    pass


class GeminiAuthError(Exception):
    """Raised when Gemini API authentication fails."""
    pass


def _build_analysis_prompt(
    company_name: str,
    ticker: str,
    title: str,
    content: str
) -> str:
    """
    Build the sentiment analysis prompt for Gemini.

    Args:
        company_name: Name of the company
        ticker: Stock ticker symbol
        title: Announcement title
        content: Announcement content

    Returns:
        str: Formatted prompt for Gemini API
    """
    return f"""You are analyzing Tel Aviv Stock Exchange (TASE) announcements to determine trading sentiment.

Company: {company_name}
Ticker: {ticker}
Announcement Title: {title}
Announcement Content: {content}

Analyze the sentiment and provide:
1. Sentiment: POSITIVE, NEGATIVE, or NEUTRAL
2. Confidence: 0.00 to 1.00
3. Reasoning: Brief explanation (2-3 sentences)

POSITIVE = likely price increase
NEGATIVE = likely price decrease
NEUTRAL = no clear directional impact

Respond ONLY with valid JSON:
{{
  "sentiment": "POSITIVE",
  "confidence": 0.85,
  "reasoning": "Strong earnings..."
}}"""


def _parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """
    Parse and validate Gemini API response.

    Args:
        response_text: Raw response text from Gemini

    Returns:
        Dict with sentiment, confidence, and reasoning

    Raises:
        ValueError: If response is invalid JSON or missing required fields
    """
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        log_system_event(
            level='ERROR',
            component='gemini_client',
            message='Failed to parse JSON response from Gemini',
            metadata={'response': response_text, 'error': str(e)}
        )
        raise ValueError(f"Failed to parse JSON response: {e}")

    # Validate required fields
    required_fields = ['sentiment', 'confidence', 'reasoning']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        log_system_event(
            level='ERROR',
            component='gemini_client',
            message='Missing required fields in Gemini response',
            metadata={'response': data, 'missing_fields': missing_fields}
        )
        raise ValueError(f"Missing required field(s): {', '.join(missing_fields)}")

    # Validate sentiment value
    valid_sentiments = ['POSITIVE', 'NEGATIVE', 'NEUTRAL']
    if data['sentiment'] not in valid_sentiments:
        log_system_event(
            level='WARNING',
            component='gemini_client',
            message='Invalid sentiment value in Gemini response',
            metadata={'sentiment': data['sentiment'], 'expected': valid_sentiments}
        )

    # Validate confidence range
    if not isinstance(data['confidence'], (int, float)) or not 0 <= data['confidence'] <= 1:
        log_system_event(
            level='WARNING',
            component='gemini_client',
            message='Invalid confidence value in Gemini response',
            metadata={'confidence': data['confidence']}
        )

    return data


def _is_rate_limit_error(error_message: str) -> bool:
    """
    Check if error message indicates rate limiting.

    Args:
        error_message: Error message string

    Returns:
        bool: True if error is rate limit related
    """
    error_lower = error_message.lower()
    rate_limit_indicators = ['429', 'rate limit', 'quota', 'exhausted']
    return any(indicator in error_lower for indicator in rate_limit_indicators)


def _is_auth_error(error_message: str) -> bool:
    """
    Check if error message indicates authentication failure.

    Args:
        error_message: Error message string

    Returns:
        bool: True if error is authentication related
    """
    error_lower = error_message.lower()
    auth_indicators = ['401', 'api key', 'authentication', 'unauthorized']
    return any(indicator in error_lower for indicator in auth_indicators)


def analyze_announcement_sentiment(
    company_name: str,
    ticker: str,
    title: str,
    content: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Analyze TASE announcement sentiment using Gemini 1.5 Flash.

    Makes API call to Gemini with retry logic for rate limiting.
    Returns sentiment classification, confidence score, and reasoning.

    Args:
        company_name: Name of the company
        ticker: Stock ticker symbol
        title: Announcement title
        content: Announcement content
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        Dict with keys:
            - sentiment: 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'
            - confidence: float between 0.0 and 1.0
            - reasoning: str explanation of the sentiment

    Raises:
        GeminiRateLimitError: If rate limit exceeded after max retries
        GeminiAuthError: If API authentication fails
        ValueError: If response format is invalid
        Exception: For other API errors

    Example:
        >>> result = analyze_announcement_sentiment(
        ...     company_name="Bank Leumi",
        ...     ticker="LUMI",
        ...     title="Q4 Earnings",
        ...     content="15% profit increase..."
        ... )
        >>> print(result)
        {
            'sentiment': 'POSITIVE',
            'confidence': 0.85,
            'reasoning': 'Strong earnings growth...'
        }
    """
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        log_system_event(
            level='ERROR',
            component='gemini_client',
            message='GEMINI_API_KEY environment variable not set'
        )
        raise GeminiAuthError("GEMINI_API_KEY environment variable not set")

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Build prompt
    prompt = _build_analysis_prompt(company_name, ticker, title, content)

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            log_system_event(
                level='INFO',
                component='gemini_client',
                message=f'Calling Gemini API (attempt {attempt + 1}/{max_retries})',
                metadata={
                    'company_name': company_name,
                    'ticker': ticker,
                    'title': title
                }
            )

            response = model.generate_content(prompt)
            result = _parse_gemini_response(response.text)

            log_system_event(
                level='INFO',
                component='gemini_client',
                message='Successfully analyzed sentiment',
                metadata={
                    'company_name': company_name,
                    'ticker': ticker,
                    'sentiment': result['sentiment'],
                    'confidence': result['confidence']
                }
            )

            return result

        except Exception as e:
            error_message = str(e)
            last_error = e

            # Check for authentication errors (don't retry)
            if _is_auth_error(error_message):
                log_system_event(
                    level='ERROR',
                    component='gemini_client',
                    message='Gemini authentication failed',
                    metadata={'error': error_message}
                )
                raise GeminiAuthError(f"Authentication failed: {error_message}")

            # Check for rate limit errors (retry with backoff)
            if _is_rate_limit_error(error_message):
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt
                    log_system_event(
                        level='WARNING',
                        component='gemini_client',
                        message=f'Rate limit hit, retrying in {backoff_time}s',
                        metadata={
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'backoff_seconds': backoff_time
                        }
                    )
                    time.sleep(backoff_time)
                    continue
                else:
                    log_system_event(
                        level='ERROR',
                        component='gemini_client',
                        message='Rate limit exceeded, max retries reached',
                        metadata={'max_retries': max_retries}
                    )
                    raise GeminiRateLimitError(
                        f"Rate limit exceeded after {max_retries} retries: {error_message}"
                    )

            # For other errors, log and re-raise
            log_system_event(
                level='ERROR',
                component='gemini_client',
                message='Gemini API call failed',
                metadata={
                    'error': error_message,
                    'attempt': attempt + 1,
                    'max_retries': max_retries
                }
            )
            raise

    # Should not reach here, but just in case
    raise last_error
