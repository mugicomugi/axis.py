"""AXIS client exceptions."""


class AxisError(Exception):
    """Base exception for AXIS client."""


class AxisAuthError(AxisError):
    """Authentication failed (invalid or expired token)."""


class AxisTokenExpiredError(AxisAuthError):
    """Token has expired and cannot be refreshed via API."""


class AxisConnectionError(AxisError):
    """WebSocket connection failed."""


class AxisConnectionLimitError(AxisConnectionError):
    """Maximum simultaneous connections exceeded."""
