"""
ID generation utilities.

Provides deterministic or random unique identifiers for domain objects.
"""

import uuid


def generate_id() -> str:
    """Return a new random UUID4 string."""
    return str(uuid.uuid4())
