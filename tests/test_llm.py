from unittest.mock import patch
from strava_agent.llm import get_llm

def test_get_llm():
    """Test that get_llm initializes ChatOllama with correct parameters."""
    model_name = "test-model"
    temp = 0.5
    
    with patch("strava_agent.llm.ChatOllama") as mock_chat:
        get_llm(model=model_name, temperature=temp)
        mock_chat.assert_called_once_with(model=model_name, temperature=temp)