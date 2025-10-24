"""Socket.IO configuration and helpers for real-time updates."""

from typing import Any, Dict, Optional

import socketio

# Shared Socket.IO server instance used across the backend
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)


async def emit_progress(
    event: str,
    payload: Dict[str, Any],
    *,
    room: Optional[str] = "impact_cards",
) -> None:
    """Emit a structured progress event to the specified room."""

    await sio.emit(event, payload, room=room)

