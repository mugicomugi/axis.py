"""Tests for axis.auth module."""

import json
import base64

import pytest

from axis.auth import decode_token_payload
from axis.exceptions import AxisAuthError


def _make_jwt(payload: dict) -> str:
    """Create a minimal unsigned JWT for testing."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fake-signature").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


def test_decode_token_payload():
    payload = {"sub": "user123", "exp": 1700000000, "channels": ["eew", "quake-one"]}
    token = _make_jwt(payload)
    decoded = decode_token_payload(token)
    assert decoded["sub"] == "user123"
    assert decoded["exp"] == 1700000000
    assert "eew" in decoded["channels"]


def test_decode_invalid_token():
    with pytest.raises(AxisAuthError):
        decode_token_payload("not-a-jwt")


def test_decode_corrupt_payload():
    with pytest.raises(AxisAuthError):
        decode_token_payload("header.!!!invalid!!!.signature")
