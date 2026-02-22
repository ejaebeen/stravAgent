import os
import threading
import requests
from http.server import HTTPServer
from unittest.mock import patch, MagicMock
from strava_agent.authenticate import update_env_file, TokenHandler, authenticate

def test_update_env_file(tmp_path):
    """Test updating the .env file with new tokens."""
    # Create a dummy .env file
    env_file = tmp_path / ".env"
    env_file.write_text("STRAVA_ACCESS_TOKEN=old\nOTHER_VAR=keep")
    
    # Change working directory to tmp_path so Path(".env") works
    cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        update_env_file("new_access", "new_refresh", 123456)
        
        content = env_file.read_text()
        assert "STRAVA_ACCESS_TOKEN=new_access" in content
        assert "STRAVA_REFRESH_TOKEN=new_refresh" in content
        assert "STRAVA_EXPIRES_AT=123456" in content
        assert "OTHER_VAR=keep" in content
    finally:
        os.chdir(cwd)

def test_token_handler():
    """Test the HTTP handler receives the code."""
    server = HTTPServer(('localhost', 0), TokenHandler)
    server.authorization_code = None
    port = server.server_port
    
    def run_server():
        server.handle_request()
        
    t = threading.Thread(target=run_server)
    t.start()
    
    # Make request
    requests.get(f"http://localhost:{port}/?code=my_secret_code")
    t.join()
    
    assert server.authorization_code == "my_secret_code"
    server.server_close()

def test_authenticate_missing_creds(mock_env_vars, monkeypatch):
    """Test authenticate returns None if creds are missing."""
    # Patch the module-level variables directly since they are loaded at import time
    with patch("strava_agent.authenticate.CLIENT_ID", None), \
         patch("strava_agent.authenticate.CLIENT_SECRET", None):
        result = authenticate()
        assert result is None