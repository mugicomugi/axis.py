"""AXIS WebSocket client with automatic reconnection."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import websocket

from .auth import get_server_list, refresh_token
from .exceptions import AxisConnectionError, AxisConnectionLimitError
from .parser import MessageType, parse_message

logger = logging.getLogger("axis")

# Exponential backoff defaults
_INITIAL_DELAY = 0.2  # 200ms
_MAX_DELAY = 60.0  # 60s
_MAX_RETRIES = 10
_BACKOFF_FACTOR = 2


class AxisClient:
    """Client for the AXIS real-time information delivery service.

    Parameters
    ----------
    token:
        AXIS access token (JWT).
    auto_reconnect:
        Enable automatic reconnection with exponential backoff.
    max_retries:
        Maximum number of consecutive reconnection attempts.
    ping_interval:
        Heartbeat interval in seconds (default 60).
    """

    def __init__(
        self,
        token: str,
        *,
        auto_reconnect: bool = True,
        max_retries: int = _MAX_RETRIES,
        ping_interval: int = 60,
    ) -> None:
        self._token = token
        self._auto_reconnect = auto_reconnect
        self._max_retries = max_retries
        self._ping_interval = ping_interval

        self._handlers: Dict[str, List[Callable]] = {}
        self._global_handlers: List[Callable] = []
        self._on_connect_handlers: List[Callable] = []
        self._on_error_handlers: List[Callable] = []
        self._on_close_handlers: List[Callable] = []

        self._ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._connected = False
        self._hello_received = False
        self._retry_count = 0

    # ------------------------------------------------------------------
    # Decorator / handler registration
    # ------------------------------------------------------------------

    def on(self, channel: str) -> Callable:
        """Register a handler for a specific channel via decorator.

        Usage::

            @client.on("eew")
            def handle_eew(message):
                ...
        """
        def decorator(func: Callable) -> Callable:
            self._handlers.setdefault(channel, []).append(func)
            return func
        return decorator

    def on_all(self, func: Callable) -> Callable:
        """Register a handler that receives all messages regardless of channel."""
        self._global_handlers.append(func)
        return func

    def on_connect(self, func: Callable) -> Callable:
        """Register a handler called when WebSocket connection is established."""
        self._on_connect_handlers.append(func)
        return func

    def on_error(self, func: Callable) -> Callable:
        """Register a handler called on WebSocket errors."""
        self._on_error_handlers.append(func)
        return func

    def on_close(self, func: Callable) -> Callable:
        """Register a handler called when WebSocket connection is closed."""
        self._on_close_handlers.append(func)
        return func

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def refresh_token(self) -> str:
        """Refresh the access token via the AXIS API.

        Updates the internal token and returns the new value.
        """
        self._token = refresh_token(self._token)
        return self._token

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _get_ws_url(self) -> str:
        servers = get_server_list(self._token)
        url = servers[0]
        if not url.lower().startswith("wss://"):
            raise AxisConnectionError(
                f"Server returned non-secure WebSocket URL: {url!r}. "
                "Only wss:// connections are allowed."
            )
        return url + "/socket"

    def _build_ws(self, url: str) -> websocket.WebSocketApp:
        return websocket.WebSocketApp(
            url,
            header=[f"Authorization: Bearer {self._token}"],
            on_open=self._ws_on_open,
            on_message=self._ws_on_message,
            on_error=self._ws_on_error,
            on_close=self._ws_on_close,
        )

    def start(self) -> None:
        """Connect to AXIS and start receiving messages (blocking).

        This method blocks until :meth:`stop` is called or the maximum
        number of reconnection attempts is exceeded.
        """
        self._stop_event.clear()
        self._run_loop()

    def start_async(self) -> threading.Thread:
        """Connect to AXIS in a background thread (non-blocking).

        Returns the daemon thread.
        """
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        """Gracefully disconnect from AXIS."""
        self._stop_event.set()
        if self._ws is not None:
            self._ws.close()

    def wait(self, timeout: Optional[float] = None) -> None:
        """Wait for the background thread to finish (use after ``start_async``)."""
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    # ------------------------------------------------------------------
    # Internal run loop with exponential backoff
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        self._retry_count = 0
        delay = _INITIAL_DELAY

        while not self._stop_event.is_set():
            try:
                url = self._get_ws_url()
            except Exception as exc:
                logger.error("Failed to fetch server list: %s", exc)
                if not self._auto_reconnect or self._retry_count >= self._max_retries:
                    raise AxisConnectionError(str(exc)) from exc
                self._retry_count += 1
                logger.info("Retrying in %.1fs (%d/%d)", delay, self._retry_count, self._max_retries)
                self._stop_event.wait(delay)
                delay = min(delay * _BACKOFF_FACTOR, _MAX_DELAY)
                continue

            self._hello_received = False
            self._ws = self._build_ws(url)

            try:
                self._ws.run_forever(ping_interval=self._ping_interval)
            except Exception as exc:
                logger.error("WebSocket error: %s", exc)

            # If stop was requested, exit the loop
            if self._stop_event.is_set():
                break

            # Reconnect logic
            if not self._auto_reconnect:
                break

            self._retry_count += 1
            if self._retry_count > self._max_retries:
                logger.error("Max reconnection attempts (%d) exceeded", self._max_retries)
                break

            logger.info("Reconnecting in %.1fs (%d/%d)", delay, self._retry_count, self._max_retries)
            self._stop_event.wait(delay)
            delay = min(delay * _BACKOFF_FACTOR, _MAX_DELAY)

    # ------------------------------------------------------------------
    # WebSocket callbacks
    # ------------------------------------------------------------------

    def _ws_on_open(self, ws: websocket.WebSocketApp) -> None:
        logger.info("WebSocket connected")
        self._connected = True

    def _ws_on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        # The server sends a bare "hello" string on connection (not JSON)
        if not self._hello_received:
            if message.strip('"').strip() == "hello":
                self._hello_received = True
                # Reset retry counter on successful connection
                self._retry_count = 0
                logger.info("Received hello, connection established")
                for handler in self._on_connect_handlers:
                    try:
                        handler()
                    except Exception:
                        logger.exception("Error in on_connect handler")
                return

        # Ignore heartbeat echo
        if message.strip('"').strip() == "hb":
            return

        # Parse JSON message
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            sanitized = message[:100].replace("\n", "\\n").replace("\r", "\\r")
            logger.warning("Non-JSON message received: %s", sanitized)
            return

        # Check for connection limit error
        if isinstance(data, str) and "Connection limit exceeded" in data:
            logger.error(data)
            for handler in self._on_error_handlers:
                try:
                    handler(AxisConnectionLimitError(data))
                except Exception:
                    logger.exception("Error in on_error handler")
            return

        # Extract channel and message payload
        # The format is {"data": {"channel": "...", "message": {...}}}
        # or direct {"channel": "...", "message": {...}}
        if "data" in data:
            inner = data["data"]
        else:
            inner = data

        channel = inner.get("channel", "")
        msg_payload = inner.get("message", inner)

        # Parse into typed model
        parsed = parse_message(channel, msg_payload)

        # Dispatch to channel-specific handlers
        for handler in self._handlers.get(channel, []):
            try:
                handler(parsed)
            except Exception:
                logger.exception("Error in handler for channel '%s'", channel)

        # Dispatch to global handlers
        for handler in self._global_handlers:
            try:
                handler(channel, parsed)
            except Exception:
                logger.exception("Error in global handler")

    def _ws_on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.error("WebSocket error: %s", error)
        self._connected = False
        for handler in self._on_error_handlers:
            try:
                handler(error)
            except Exception:
                logger.exception("Error in on_error handler")

    def _ws_on_close(self, ws: websocket.WebSocketApp, close_status_code: Any = None, close_msg: str = "") -> None:
        logger.info("WebSocket closed (code=%s, msg=%s)", close_status_code, close_msg)
        self._connected = False
        for handler in self._on_close_handlers:
            try:
                handler(close_status_code, close_msg)
            except Exception:
                logger.exception("Error in on_close handler")
