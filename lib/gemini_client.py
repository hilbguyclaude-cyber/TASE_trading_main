"""
Gemini API client for sentiment analysis.

Provides integration with Google's Gemini 1.5 Flash model to analyze
TASE announcements and determine trading sentiment with confidence scores.
"""

import os
import json
from typing import Dict, Any
import google.generativeai as genai
import google.api_core.exceptions
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
    prompt = _build_analysis_prompt(company_name, title, content)

    try:
        log_system_event(
            level='INFO',
            component='gemini_client',
            message='Calling Gemini API',
            metadata={
                'company_name': company_name,
                'ticker': ticker,
                'title': title
            }
        )

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

        # Validate required fields exist
        if 'sentiment' not in response_json or 'reasoning' not in response_json:
            error_message = f"Missing required fields in response: {response_json}"
            log_system_event(
                level='ERROR',
                component='gemini_client',
                message='Gemini response missing required fields',
                metadata={'response': response_json}
            )
            raise ValueError(f"Invalid response structure: missing required fields")

        # Normalize sentiment with exact matching
        raw_sentiment = response_json.get('sentiment', '').strip().lower()
        if raw_sentiment == 'positive sentiment':
            sentiment = 'positive'
        elif raw_sentiment == 'negative sentiment':
            sentiment = 'negative'
        elif raw_sentiment == 'neutral':
            sentiment = 'neutral'
        else:
            # Log unexpected format but default to neutral
            log_system_event(
                level='WARNING',
                component='gemini_client',
                message=f'Unexpected sentiment format: {raw_sentiment}',
                metadata={'raw_sentiment': raw_sentiment}
            )
            sentiment = 'neutral'

        result = {
            'sentiment': sentiment,
            'reasoning': response_json.get('reasoning', ''),
            'confidence': None,  # Not returned by user's prompt
            'raw_response': response_json  # Store full response for audit
        }

        log_system_event(
            level='INFO',
            component='gemini_client',
            message='Successfully analyzed sentiment',
            metadata={
                'company_name': company_name,
                'ticker': ticker,
                'sentiment': result['sentiment']
            }
        )

        return result

    except google.api_core.exceptions.DeadlineExceeded:
        error_message = f"Gemini API timeout after 10s for {company_name}"
        log_system_event(
            level='ERROR',
            component='gemini_client',
            message=error_message
        )
        raise TimeoutError(error_message)

    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON response: {response.text}"
        log_system_event(
            level='ERROR',
            component='gemini_client',
            message='Gemini returned invalid JSON',
            metadata={'error': str(e), 'response': response.text}
        )
        raise ValueError(f"Invalid JSON from Gemini: {str(e)}")

    except Exception as e:
        error_message = str(e)

        # Check for authentication errors
        if _is_auth_error(error_message):
            log_system_event(
                level='ERROR',
                component='gemini_client',
                message='Gemini authentication failed',
                metadata={'error': error_message}
            )
            raise GeminiAuthError(f"Authentication failed: {error_message}")

        # For other errors, log and re-raise
        log_system_event(
            level='ERROR',
            component='gemini_client',
            message='Gemini API call failed',
            metadata={'error': error_message}
        )
        raise
