from datetime import datetime
from strava_agent.prompts import get_system_prompt

def test_get_system_prompt():
    """Test that the system prompt contains the current date and critical instructions."""
    prompt = get_system_prompt()
    today = datetime.now().strftime("%Y-%m-%d")
    
    assert today in prompt
    assert "CRITICAL" in prompt
    assert "get_activity_information" in prompt