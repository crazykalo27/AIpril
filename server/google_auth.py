"""Google OAuth2 and Calendar API helpers.

Web-based flow: /auth/start → Google consent → /auth/callback → token.json.
"""
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

_flow: Flow | None = None


def is_authenticated(token_file: Path) -> bool:
    """Check if token.json exists with valid or refreshable credentials."""
    if not token_file.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        if creds.valid:
            return True
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, "w") as f:
                f.write(creds.to_json())
            return True
    except Exception:
        pass
    return False


def get_auth_url(credentials_file: Path, redirect_uri: str) -> str | None:
    """Create OAuth flow and return the Google authorization URL."""
    global _flow
    if not credentials_file.exists():
        return None
    _flow = Flow.from_client_secrets_file(
        str(credentials_file),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, _ = _flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def handle_auth_callback(code: str, token_file: Path) -> bool:
    """Exchange authorization code for tokens. Returns True on success."""
    global _flow
    if not _flow:
        return False
    try:
        _flow.fetch_token(code=code)
        creds = _flow.credentials
        with open(token_file, "w") as f:
            f.write(creds.to_json())
        _flow = None
        return True
    except Exception as e:
        print(f"[Auth] Token exchange failed: {e}")
        _flow = None
        return False


def get_credentials(credentials_file: Path, token_file: Path) -> Credentials | None:
    """Load or refresh Google credentials. Returns None if not authenticated."""
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None

    if creds:
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return creds


def create_calendar_event(
    creds: Credentials,
    summary: str,
    description: str,
    start_time: str,
    end_time: str,
) -> str | None:
    """Create a Google Calendar event. Returns event ID or None."""
    service = build("calendar", "v3", credentials=creds)
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "UTC"},
        "end": {"dateTime": end_time, "timeZone": "UTC"},
    }
    event = service.events().insert(calendarId="primary", body=body).execute()
    return event.get("id")


def list_calendar_events(
    creds: Credentials,
    time_min: str,
    time_max: str,
) -> list[dict]:
    """List calendar events in time range."""
    service = build("calendar", "v3", credentials=creds)
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = []
    for item in events_result.get("items", []):
        start = item.get("start", {}).get("dateTime", item.get("start", {}).get("date", ""))
        end = item.get("end", {}).get("dateTime", item.get("end", {}).get("date", ""))
        events.append({
            "id": item.get("id", ""),
            "summary": item.get("summary", ""),
            "start": start,
            "end": end,
        })
    return events
