"""
Tests for Gemini API client.

Tests sentiment analysis functionality with mocked API responses.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from lib.gemini_client import (
    analyze_announcement_sentiment,
    GeminiAuthError
)


def test_analyze_announcement_sentiment_success():
    """Test successful sentiment analysis with mocked Gemini API."""
    # Mock response from Gemini API
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "positive sentiment",
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
    assert result['sentiment'] == 'positive'
    assert result['confidence'] is None
    assert 'earnings' in result['reasoning'].lower()

    # Verify API was called
    mock_genai.GenerativeModel.assert_called_once_with('gemini-1.5-flash')
    mock_model.generate_content.assert_called_once()


def test_analyze_announcement_sentiment_negative():
    """Test negative sentiment analysis."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "negative sentiment",
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

    assert result['sentiment'] == 'negative'
    assert result['confidence'] is None


def test_analyze_announcement_sentiment_neutral():
    """Test neutral sentiment analysis."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "sentiment": "neutral",
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

    assert result['sentiment'] == 'neutral'
    assert result['confidence'] is None


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
                with pytest.raises(ValueError, match="Invalid JSON from Gemini"):
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
        "sentiment": "positive sentiment"
        # Missing reasoning
    })

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    with patch('lib.gemini_client.genai') as mock_genai:
        mock_genai.GenerativeModel.return_value = mock_model
        with patch('lib.gemini_client.os.getenv', return_value='fake_api_key'):
            with patch('lib.gemini_client.log_system_event'):
                with pytest.raises(ValueError, match="missing required fields"):
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
        "sentiment": "positive sentiment",
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

        # Verify prompt contains required elements (NOT ticker - removed per Task 4)
        assert "Bank Leumi" in prompt
        assert "Earnings Report" in prompt
        assert "Strong quarterly results" in prompt

        # Verify 3-part structure markers
        assert "Persona:" in prompt
        assert "Company Name:" in prompt
        assert "Response Format:" in prompt

        # Verify new sentiment format phrases are mentioned
        assert "positive sentiment" in prompt
        assert "negative sentiment" in prompt
        assert "neutral" in prompt
        assert "Tel Aviv Stock Exchange" in prompt
