"""
Logging configuration for the application.

Sets up structured console logging with a consistent format.
Call ``setup_logging`` once at application startup.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with a standard format.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger for a module.

    Args:
        name: Typically ``__name__`` of the calling module.
    """
    return logging.getLogger(name)
