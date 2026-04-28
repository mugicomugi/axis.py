"""AXIS token authentication helpers."""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional

import requests

from .exceptions import AxisAuthError, AxisTokenExpiredError

BASE_URL = "https://axis.prioris.jp"
TOKEN_REFRESH_URL = f"{BASE_URL}/api/token/refresh/"
SERVER_LIST_URL = f"{BASE_URL}/api/server/list/"


def _auth_header(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def decode_token_payload(token: str) -> Dict[str, Any]:
    """Decode the JWT payload without verifying the signature.

    This is used only for reading expiration and metadata locally.

    .. warning::

        The signature is **not** verified. Do **not** use the returned
        payload for authentication or authorization decisions.  An
        attacker can craft an arbitrary payload without possessing the
        signing key.  This helper is intended solely for local
        inspection of token metadata (e.g. expiration time).
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise AxisAuthError("Invalid JWT token format")
    payload_b64 = parts[1]
    # Add padding if needed
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception as exc:
        raise AxisAuthError(f"Failed to decode token payload: {exc}") from exc


def refresh_token(token: str, timeout: float = 10.0) -> str:
    """Refresh the AXIS access token.

    Returns the new token string.  If the token is not yet due for refresh,
    the current token is returned unchanged.

    Raises:
        AxisTokenExpiredError: Contract has expired (HTTP 402).
        AxisAuthError: Other authentication errors.
    """
    try:
        resp = requests.get(
            TOKEN_REFRESH_URL,
            headers=_auth_header(token),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise AxisAuthError(f"Token refresh request failed: {exc}") from exc

    if resp.status_code == 402:
        raise AxisTokenExpiredError("Contract has expired. Renew at https://axis.prioris.jp/manage/token/")

    if resp.status_code != 200:
        raise AxisAuthError(f"Token refresh failed with status {resp.status_code}")

    data = resp.json()
    status = data.get("status", "")

    if status == "generate a new token":
        return data["token"]
    elif status == "not due for refresh yet":
        return data.get("token", token)
    else:
        raise AxisAuthError(f"Unexpected refresh response: {status}")


def get_server_list(token: str, timeout: float = 10.0) -> list[str]:
    """Fetch the list of available WebSocket server URLs.

    Returns a list of WSS URLs (e.g. ``["wss://ws.axis.prioris.jp"]``).
    """
    try:
        resp = requests.get(
            SERVER_LIST_URL,
            headers=_auth_header(token),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise AxisAuthError(f"Server list request failed: {exc}") from exc

    if resp.status_code != 200:
        raise AxisAuthError(f"Server list request failed with status {resp.status_code}")

    data = resp.json()
    servers = data.get("servers", [])
    if not servers:
        raise AxisAuthError("No available servers returned")
    return servers
