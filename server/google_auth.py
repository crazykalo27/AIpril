"""Google OAuth2 and Calendar API helpers."""
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_credentials(credentials_file: Path, token_file: Path) -> Credentials | None:
    """Load or refresh Google credentials."""
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif credentials_file.exists():
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)
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
    """List calendar events in time range. Returns list of {id, summary, start, end}."""
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
