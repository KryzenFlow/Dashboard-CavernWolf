"""Terminate Claw after each use and rebuild the control plane daily."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from .control_plane import daily_rebuild, terminate_after_use

_log = logging.getLogger(__name__)


async def after_use(session_id: str) -> None:
    terminate_after_use(f"session {session_id} complete")


async def daily_rebuild_loop() -> None:
    hour = int(os.environ.get("CLAW_DAILY_REBUILD_HOUR_UTC", "4"))
    while True:
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        wait_s = max(1.0, (next_run - now).total_seconds())
        _log.info("next claw daily rebuild in %.0fs", wait_s)
        await asyncio.sleep(wait_s)
        try:
            daily_rebuild()
        except Exception as exc:
            _log.critical("daily rebuild failed: %s", exc)
