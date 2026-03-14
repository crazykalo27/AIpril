"""
Network connectivity check service.

Provides a simple boolean check for internet availability.
"""

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ConnectivityService:
    """Checks whether the device has internet access."""

    def is_online(self) -> bool:
        """Return True if the system can reach the internet.

        # TODO: Implement real connectivity probe (e.g. ping Google DNS).
        """
        logger.debug("Connectivity check (stub) — returning True")
        return True
