"""
Application bootstrap.

Initializes configuration, logging, and the service container.
Call ``bootstrap()`` once at startup.
"""

from src.config.settings import load_settings, Settings
from src.config.logging_config import setup_logging, get_logger
from src.app.container import ServiceContainer

logger = get_logger(__name__)


def bootstrap() -> ServiceContainer:
    """Set up the entire application and return the service container."""
    settings = load_settings()
    setup_logging(level=settings.log_level)

    logger.info("AIpril starting up")
    logger.info("Prompt interval: %d minutes", settings.prompt_interval_minutes)

    container = ServiceContainer(settings)
    return container
