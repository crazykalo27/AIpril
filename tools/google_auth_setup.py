"""
One-time Google OAuth setup script.

Run this on your PC (not on ESP32) to get a refresh token.
Then send the token to the ESP32 via serial: set_token <token>

Prerequisites:
    pip install google-auth-oauthlib
    Download credentials.json from Google Cloud Console.

Usage:
    python tools/google_auth_setup.py
"""

import json
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = Path("credentials.json")


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

    print("\n=== SUCCESS ===")
    print(f"Refresh token: {creds.refresh_token}")
    print(f"\nSend to ESP32 via serial:")
    print(f"  set_token {creds.refresh_token}")
    print(f"\nOr add to include/secrets.h:")
    print(f'  #define GOOGLE_REFRESH_TOKEN "{creds.refresh_token}"')


if __name__ == "__main__":
    main()
