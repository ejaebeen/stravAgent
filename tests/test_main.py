import sys
from unittest.mock import patch, MagicMock
from strava_agent.__main__ import main

def test_main_auth_trigger(mock_env_vars, monkeypatch):
    """Test that authentication is triggered if token is missing."""
    # Ensure token is missing in env
    monkeypatch.delenv("STRAVA_ACCESS_TOKEN", raising=False)
    
    with patch("strava_agent.__main__.load_dotenv"), \
         patch("strava_agent.authenticate.authenticate") as mock_auth, \
         patch("strava_agent.graph.build_graph") as mock_build, \
         patch("builtins.input", side_effect=["quit"]):
        
        mock_auth.return_value = True
        mock_app = MagicMock()
        mock_build.return_value = mock_app
        
        main()
        
        mock_auth.assert_called_once()

def test_main_single_question(mock_env_vars):
    """Test running main with command line arguments (single question mode)."""
    test_args = ["strava-agent", "How", "many", "runs?"]
    
    with patch("strava_agent.__main__.load_dotenv"), \
         patch.object(sys, 'argv', test_args), \
         patch("strava_agent.graph.build_graph") as mock_build:
        
        mock_app = MagicMock()
        mock_build.return_value = mock_app
        
        # Mock the graph invocation result
        mock_msg = MagicMock()
        mock_msg.content = "You ran 5 times."
        mock_app.invoke.return_value = {"messages": [mock_msg]}
        
        main()
        
        # Verify invoke was called with the question
        args, _ = mock_app.invoke.call_args
        messages = args[0]["messages"]
        assert messages[-1].content == "How many runs?"

def test_main_graph_visualization(mock_env_vars):
    """Test the --graph flag."""
    with patch("strava_agent.__main__.load_dotenv"), \
         patch.object(sys, 'argv', ["strava-agent", "--graph"]), \
         patch("strava_agent.graph.build_graph") as mock_build:
        main()
        mock_build.return_value.get_graph.return_value.draw_mermaid.assert_called_once()