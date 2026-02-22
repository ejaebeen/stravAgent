import pytest
import json
import os
from unittest.mock import MagicMock, patch

# Fixture to mock user data that might be used across multiple tests
# Scope='session' means this is created once per test run
@pytest.fixture(scope="session")
def sample_user_context():
    return {
        "user_id": 12345,
        "email": "test@example.com",
        "preferences": {"language": "it", "theme": "dark"}
    }

# Fixture to load the translation file provided in context
@pytest.fixture(scope="session")
def it_translation_data():
    # Adjust path relative to the project root
    file_path = ".chainlit/translations/it.json"
    
    # Check if file exists before trying to open
    if not os.path.exists(file_path):
        # Fallback: try absolute path if running from a different location
        # Assuming the structure based on the provided file path
        base_path = "/Users/ejaebeen/Documents/playground/strava-playground/"
        file_path = os.path.join(base_path, ".chainlit/translations/it.json")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Sets up environment variables for testing."""
    monkeypatch.setenv("STRAVA_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "test_refresh")
    monkeypatch.setenv("STRAVA_CLIENT_ID", "123")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    monkeypatch.setenv("STRAVA_EXPIRES_AT", "2000000000")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.0")

@pytest.fixture
def mock_strava_client():
    """
    Mocks the Strava Client class.
    We patch it in the tools module where it is primarily used.
    """
    with patch("strava_agent.tools.Client") as mock:
        yield mock.return_value