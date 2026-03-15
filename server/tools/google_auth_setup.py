"""
One-time Google OAuth setup script for the server.

Run from server directory. Creates token.json for Google Calendar API.
Server uses token.json for calendar operations.

Prerequisites:
    pip install google-auth-oauthlib
    Download credentials.json from Google Cloud Console, place in server/

Usage:
    cd server && python tools/google_auth_setup.py
"""

from pathlib import Path

# Run from server dir; credentials.json and token.json live there
SCRIPT_DIR = Path(__file__).resolve().parent
SERVER_DIR = SCRIPT_DIR.parent
CREDENTIALS_FILE = SERVER_DIR / "credentials.json"
TOKEN_FILE = SERVER_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main() -> None:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install: pip install google-auth-oauthlib")
        return

    if not CREDENTIALS_FILE.exists():
        print(f"Missing {CREDENTIALS_FILE}")
        print("Download from: https://console.cloud.google.com/apis/credentials")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print("\n=== SUCCESS ===")
    print(f"Saved token to {TOKEN_FILE}")
    print("Server can now use Google Calendar API.")
