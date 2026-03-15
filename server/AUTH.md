# Google Calendar Authentication

## API key vs OAuth

**`GOOGLE_API_KEY` (AIzaSy...)** — A simple API key is **not** enough for Google Calendar.  
You can remove it from `.env`; it is not used for Calendar.

- API keys work for public/read-only APIs (e.g. Maps, Places).
- **Google Calendar** needs **OAuth 2.0** because it accesses a user’s personal calendar.

## What you need for Calendar

1. **OAuth 2.0 Client** (not an API key)
   - In [Google Cloud Console](https://console.cloud.google.com/apis/credentials):
   - Create **OAuth 2.0 Client ID** (Desktop app).
   - Download the JSON and save it as `credentials.json` in the `server/` folder.

2. **One-time OAuth flow**
   ```bash
   cd server
   python tools/google_auth_setup.py
   ```
   - A browser opens for you to sign in with your Google account.
   - This creates `token.json` with a refresh token.

3. **Enable the Calendar API**
   - In Google Cloud Console → APIs & Services → Enable **Google Calendar API** for your project.

## Summary

| File            | Purpose                          |
|-----------------|----------------------------------|
| `credentials.json` | OAuth client config (from Console) |
| `token.json`       | Refresh token (from setup script)   |
| `GOOGLE_API_KEY`   | Not used for Calendar              |

After setup, the server uses `credentials.json` and `token.json` for Calendar. No API key is needed for Calendar.
