import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from dotenv import load_dotenv
from stravalib.client import Client

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
PORT = 8000
REDIRECT_URI = f"http://localhost:{PORT}/"

class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle the callback from Strava."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Success! You can close this tab.</h1>")
        
        # Extract code from URL
        query = urlparse(self.path).query
        query_components = parse_qs(query)
        if "code" in query_components:
            self.server.authorization_code = query_components["code"][0]

def update_env_file(access_token, refresh_token, expires_at):
    """Update the .env file with new tokens."""
    env_path = Path(".env")
    
    # Read existing lines
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()

    new_lines = []
    keys_updated = set()
    
    updates = {
        "STRAVA_ACCESS_TOKEN": access_token,
        "STRAVA_REFRESH_TOKEN": refresh_token,
        "STRAVA_EXPIRES_AT": str(expires_at)
    }

    for line in lines:
        key = line.split("=")[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}\n")
            keys_updated.add(key)
        else:
            new_lines.append(line)
            
    for key, value in updates.items():
        if key not in keys_updated:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')
            new_lines.append(f"{key}={value}\n")
            
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    
    print(f"Updated {env_path} with new tokens.")

def authenticate():
    """Run the Strava OAuth flow."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env")
        return None

    client = Client()
    authorize_url = client.authorization_url(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=["read", "activity:read_all", "profile:read_all"]
    )

    print(f"Opening browser to: {authorize_url}")
    webbrowser.open(authorize_url)

    print(f"Listening on port {PORT}...")
    server = HTTPServer(('localhost', PORT), TokenHandler)
    server.authorization_code = None

    # Wait for the request
    while server.authorization_code is None:
        server.handle_request()

    print("\nCode received! Exchanging for tokens...")
    token_response = client.exchange_code_for_token(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        code=server.authorization_code
    )
    
    # Update .env file
    update_env_file(
        token_response['access_token'],
        token_response['refresh_token'],
        token_response['expires_at']
    )
    
    # Update current process environment variables
    os.environ["STRAVA_ACCESS_TOKEN"] = token_response['access_token']
    os.environ["STRAVA_REFRESH_TOKEN"] = token_response['refresh_token']
    os.environ["STRAVA_EXPIRES_AT"] = str(token_response['expires_at'])

    return token_response

def main():
    authenticate()

if __name__ == "__main__":
    main()