"""
Tests for Gemini API client.

Tests sentiment analysis functionality with mocked API responses.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from lib.gemini_client import (
    analyze_announcement_sentiment,
    GeminiRateLimitError,
    GeminiAuthError
)


def test_analyze_announcement_sentiment_success():
    """Test successful sentiment analysis with mocked Gemini API."""
    # Mock response from Gemini API
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "POSITIVE",
        "confidence": 0.85,
        "reasoning": "Strong earnings report indicates potential price increase."
    })

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                result = analyze_announcement_sentiment(
                    company_name="Bank Leumi",
                    ticker="LUMI",
                    title="Q4 Earnings Report",
                    content="Bank Leumi reports 15% increase in quarterly profits..."
                )

    # Verify the result
    assert result['sentiment'] == 'POSITIVE'
    assert result['confidence'] == 0.85
    assert 'earnings' in result['reasoning'].lower()

    # Verify API was called
    mock_genai.GenerativeModel.assert_called_once_with('gemini-1.5-flash')
    mock_model.generate_content.assert_called_once()


def test_analyze_announcement_sentiment_negative():
    """Test negative sentiment analysis."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "NEGATIVE",
        "confidence": 0.75,
        "reasoning": "Regulatory investigation may lead to fines and reputational damage."
    })

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                result = analyze_announcement_sentiment(
                    company_name="Test Corp",
                    ticker="TEST",
                    title="Regulatory Investigation",
                    content="Company under investigation for compliance issues..."
                )

    assert result['sentiment'] == 'NEGATIVE'
    assert result['confidence'] == 0.75


def test_analyze_announcement_sentiment_neutral():
    """Test neutral sentiment analysis."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "NEUTRAL",
        "confidence": 0.60,
        "reasoning": "Administrative change with no clear impact on business operations."
    })

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                result = analyze_announcement_sentiment(
                    company_name="Test Corp",
                    ticker="TEST",
                    title="Board Member Appointment",
                    content="New board member appointed..."
                )

    assert result['sentiment'] == 'NEUTRAL'
    assert result['confidence'] == 0.60


def test_analyze_announcement_sentiment_with_retry():
    """Test retry logic when rate limit is hit."""
    # First call returns rate limit error, second succeeds
    mock_response_success = MagicMock()
    mock_response_success.text = json.dumps({
        "sentiment": "POSITIVE",
        "confidence": 0.80,
        "reasoning": "Good news after retry."
    })

    mock_model = MagicMock()
    # First call raises rate limit exception
    mock_model.generate_content.side_effect = [
        Exception("429 Resource has been exhausted"),
        mock_response_success
    ]

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.time.sleep'):  # Mock sleep to speed up test
                with patch('lib.gemini_client.log_system_event') as mock_log:
                    result = analyze_announcement_sentiment(
                        company_name="Test Corp",
                        ticker="TEST",
                        title="Test",
                        content="Test content"
                    )

    # Should succeed after retry
    assert result['sentiment'] == 'POSITIVE'
    assert result['confidence'] == 0.80

    # Should have called API twice
    assert mock_model.generate_content.call_count == 2

    # Should have logged the retry
    assert mock_log.call_count >= 1


def test_analyze_announcement_sentiment_rate_limit_error():
    """Test that rate limit errors are properly raised after max retries."""
    mock_model = MagicMock()
    # Always raise rate limit error
    mock_model.generate_content.side_effect = Exception("429 rate limit exceeded")

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.time.sleep'):  # Mock sleep to speed up test
                with patch('lib.gemini_client.log_system_event'):
                    with pytest.raises(GeminiRateLimitError):
                        analyze_announcement_sentiment(
                            company_name="Test Corp",
                            ticker="TEST",
                            title="Test",
                            content="Test content",
                            max_retries=3
                        )

    # Should have called API max_retries times
    assert mock_model.generate_content.call_count == 3


def test_analyze_announcement_sentiment_auth_error():
    """Test that authentication errors are properly raised."""
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("401 API key not valid")

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                with pytest.raises(GeminiAuthError):
                    analyze_announcement_sentiment(
                        company_name="Test Corp",
                        ticker="TEST",
                        title="Test",
                        content="Test content"
                    )


def test_analyze_announcement_sentiment_invalid_json():
    """Test handling of invalid JSON response."""
    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON"

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                with pytest.raises(ValueError, match="Failed to parse JSON response"):
                    analyze_announcement_sentiment(
                        company_name="Test Corp",
                        ticker="TEST",
                        title="Test",
                        content="Test content"
                    )


def test_analyze_announcement_sentiment_missing_fields():
    """Test handling of response with missing required fields."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "POSITIVE"
        # Missing confidence and reasoning
    })

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                with pytest.raises(ValueError, match="Missing required field"):
                    analyze_announcement_sentiment(
                        company_name="Test Corp",
                        ticker="TEST",
                        title="Test",
                        content="Test content"
                    )


def test_prompt_format():
    """Test that the prompt is formatted correctly."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "POSITIVE",
        "confidence": 0.85,
        "reasoning": "Test reasoning"
    })

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                analyze_announcement_sentiment(
                    company_name="Bank Leumi",
                    ticker="LUMI",
                    title="Earnings Report",
                    content="Strong quarterly results"
                )

        # Get the prompt that was passed
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]

        # Verify prompt contains all required elements
        assert "Bank Leumi" in prompt
        assert "LUMI" in prompt
        assert "Earnings Report" in prompt
        assert "Strong quarterly results" in prompt
        assert "POSITIVE" in prompt
        assert "NEGATIVE" in prompt
        assert "NEUTRAL" in prompt
        assert "Tel Aviv Stock Exchange" in prompt
