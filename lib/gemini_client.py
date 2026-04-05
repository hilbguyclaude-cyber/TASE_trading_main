"""
Gemini API client for sentiment analysis.

Provides integration with Google's Gemini 1.5 Flash model to analyze
TASE announcements and determine trading sentiment with confidence scores.
"""

import os
import json
import time
import logging
from typing import Dict, Any
import google.generativeai as genai
import google.api_core.exceptions
from lib.db import log_system_event

logger = logging.getLogger(__name__)


# Custom exceptions
class GeminiRateLimitError(Exception):
    """Raised when Gemini API rate limit is exceeded."""
    pass


class GeminiAuthError(Exception):
    """Raised when Gemini API authentication fails."""
    pass


def _build_analysis_prompt(
    company_name: str,
    title: str,
    content: str,
    additional_file_link: str = None
) -> str:
    """
    Build the analysis prompt using the user's exact 3-part format:
    1. System Instructions (Persona & Rules)
    2. User Prompt Template (Data Input)
    3. Output Formatting Instructions
    """

    # Part 1: System Instructions (The Persona & Rules)
    system_instructions = """**Persona:**
You are an expert financial analyst and quantitative trading specialist with profound expertise in the Israeli capital markets and the Tel Aviv Stock Exchange (TASE). You have comprehensive knowledge of Israeli public companies, their historical market behavior, their industry sectors, and exactly how their stock prices react to specific corporate announcements.

**Task:**
You will be provided with a corporate announcement, including its title, content, and additional reference material. Your objective is to conduct an in-depth analysis of this announcement and predict the immediate short-term impact on the company's stock price, specifically focusing on the next 60 minutes of trading.

**Analysis Criteria:**
You must evaluate the expected price action without requiring any external prompts. Base your analysis on:
1. The language, tone, materiality, and financial/business implications of the announcement.
2. Your pre-existing knowledge of the specific company, its baseline performance, and how it has historically reacted to similar news.
3. Your knowledge of similar companies, industry peers, and the broader context of the TASE.

**Output Categories:**
You must classify the sentiment into exactly one of the following three categories. Pay strict attention to the 1% threshold:
* "positive sentiment": You have a high level of confidence that the stock price will RISE by MORE THAN 1% in the next 60 minutes. This requires a strong, material catalyst.
* "negative sentiment": You have a high level of confidence that the stock price will DROP in the next 60 minutes.
* "neutral": The stock is not expected to rise by more than 1% or drop significantly. Use this if the news is already priced in, immaterial, ambiguous, or lacks the necessary confidence level for a definitive move."""

    # Part 2: User Prompt Template (The Data Input)
    file_section = f"\n**Additional File Link:** {additional_file_link}" if additional_file_link else ""

    user_prompt = f"""Please analyze the following corporate announcement and determine the short-term market reaction:

**Company Name:** {company_name}
**Announcement Title:** {title}
**Announcement Content:** {content}{file_section}"""

    # Part 3: Output Formatting Instructions
    output_format = """
**Response Format:**
You must return your analysis strictly as a JSON object with exactly two keys:
1. "sentiment": Must be exactly one of the following strings: "positive sentiment", "negative sentiment", or "neutral".
2. "reasoning": A concise, 3 to 4 sentence analytical justification for your decision. Explain the specific catalyst, why it relates to the company's TASE history, and why it does or does not meet the strict >1% movement threshold within a 60-minute window."""

    # Combine all parts
    return f"{system_instructions}\n\n{user_prompt}\n{output_format}"


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
    content: str
) -> Dict[str, Any]:
    """
    Call Gemini API with explicit timeout and normalize response.

    Returns:
        Dict with:
        - sentiment: str - 'positive', 'negative', or 'neutral' (normalized)
        - reasoning: str - Explanation of sentiment
        - confidence: None - Not returned by current prompt
        - raw_response: dict - Full API response for audit

    Raises:
        TimeoutError: If Gemini API exceeds 10s timeout
        ValueError: If response parsing fails
    """
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("[GEMINI] GEMINI_API_KEY environment variable not set")
        raise GeminiAuthError("GEMINI_API_KEY environment variable not set")

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    try:
        prompt = _build_analysis_prompt(company_name, title, content)

        # Call Gemini with 10-second timeout
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.1,
                'top_p': 0.95,
                'max_output_tokens': 500,
            },
            request_options={
                'timeout': 10  # 10 second timeout
            }
        )

        # Parse JSON response
        response_json = json.loads(response.text)

        # Normalize sentiment: "positive sentiment" → "positive"
        raw_sentiment = response_json.get('sentiment', '').lower()
        if 'positive' in raw_sentiment:
            sentiment = 'positive'
        elif 'negative' in raw_sentiment:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        return {
            'sentiment': sentiment,
            'reasoning': response_json.get('reasoning', ''),
            'confidence': None,  # Not returned by user's prompt
            'raw_response': response_json  # Store full response for audit
        }

    except google.api_core.exceptions.DeadlineExceeded:
        logger.error(f"[GEMINI] API timeout (>10s) for {company_name}")
        raise TimeoutError(f"Gemini API timeout after 10s")

    except json.JSONDecodeError as e:
        logger.error(f"[GEMINI] Invalid JSON response: {response.text}")
        raise ValueError(f"Invalid JSON from Gemini: {str(e)}")
