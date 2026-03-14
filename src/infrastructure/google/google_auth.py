"""
Google OAuth2 authentication handler.

Manages the credential lifecycle: loading cached tokens,
running the OAuth consent flow, and refreshing expired tokens.
"""

from pathlib import Path
from typing import Optional

from src.config.logging_config import get_logger

logger = get_logger(__name__)

# Type alias — the real type comes from google.oauth2.credentials
Credentials = object


class GoogleAuth:
    """Handles Google OAuth2 credential acquisition and refresh."""

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        scopes: list[str] | None = None,
    ) -> None:
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._scopes = scopes or []
        self._creds: Optional[Credentials] = None

    def authenticate(self) -> Credentials:
        """Return valid credentials, running the OAuth flow if needed.

        # TODO: Implement full OAuth2 flow using google-auth-oauthlib.
        """
        logger.info("Google authentication (stub) — returning placeholder")
        return object()

    def _load_cached_token(self) -> Optional[Credentials]:
        """Attempt to load a previously saved token from disk.

        # TODO: Deserialize token.json using google.oauth2.credentials.
        """
        if self._token_path.exists():
            logger.debug("Found cached token at %s", self._token_path)
            return None  # TODO: return real credentials
        return None

    def _save_token(self, creds: Credentials) -> None:
        """Persist credentials to disk for future runs.

        # TODO: Serialize token to token.json.
        """
        logger.debug("Saving token to %s (stub)", self._token_path)
