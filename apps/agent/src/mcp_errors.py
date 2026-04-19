from __future__ import annotations


PERMISSION_MESSAGE = "Darauf habe ich mit meinem Agent-Zugang leider keinen Zugriff."
_PERMISSION_MARKERS = (
    "403",
    "permission denied",
    "not permitted",
    "insufficient permissions",
)


def is_permission_error(err: Exception) -> bool:
    """Return True if an error indicates missing permissions."""
    message = str(err).lower()
    return any(marker in message for marker in _PERMISSION_MARKERS)


def user_facing_permission_message() -> str:
    return PERMISSION_MESSAGE
