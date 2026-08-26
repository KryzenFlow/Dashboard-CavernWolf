"""Dual independent watchers — either may revoke the tree without supervisor approval."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.security.token import extract_tree_id, is_revoked, revoke_tree, validate_token

WatcherFn = Callable[[dict[str, Any], dict[str, Any]], str | None]


@dataclass
class WatcherHandle:
    tree_id: str
    stop_event: threading.Event = field(default_factory=threading.Event)
    threads: list[threading.Thread] = field(default_factory=list)

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=2.0)


def _capability_watcher(
    *,
    tree_id: str,
    token: dict[str, Any],
    payload: dict[str, Any],
    interval_s: float,
    stop_event: threading.Event,
    on_revoke: Callable[[str, str], None] | None,
) -> None:
    while not stop_event.is_set():
        if is_revoked(tree_id):
            return
        ok, reason = validate_token(token)
        if not ok:
            revoke_tree(tree_id, reason=f"capability watcher: {reason}")
            if on_revoke:
                on_revoke(tree_id, reason)
            return
        time.sleep(interval_s)


def _behavior_watcher(
    *,
    tree_id: str,
    check_fn: WatcherFn,
    token: dict[str, Any],
    payload: dict[str, Any],
    interval_s: float,
    stop_event: threading.Event,
    on_revoke: Callable[[str, str], None] | None,
) -> None:
    while not stop_event.is_set():
        if is_revoked(tree_id):
            return
        reason = check_fn(token, payload)
        if reason:
            revoke_tree(tree_id, reason=f"behavior watcher: {reason}")
            if on_revoke:
                on_revoke(tree_id, reason)
            return
        time.sleep(interval_s)


def start_dual_watchers(
    token: dict[str, Any],
    payload: dict[str, Any],
    *,
    behavior_check: WatcherFn | None = None,
    interval_s: float = 0.5,
    on_revoke: Callable[[str, str], None] | None = None,
) -> WatcherHandle:
    """
    Side 1 — behavioral/process policy hook.
    Side 2 — capability/token re-validation.
    Either side calling revoke_tree kills the entire tree.
    """
    tree_id = extract_tree_id(token) or ""
    handle = WatcherHandle(tree_id=tree_id)

    cap_thread = threading.Thread(
        target=_capability_watcher,
        kwargs={
            "tree_id": tree_id,
            "token": token,
            "payload": payload,
            "interval_s": interval_s,
            "stop_event": handle.stop_event,
            "on_revoke": on_revoke,
        },
        daemon=True,
        name=f"watcher-cap-{tree_id[:8]}",
    )
    handle.threads.append(cap_thread)

    if behavior_check is not None:
        beh_thread = threading.Thread(
            target=_behavior_watcher,
            kwargs={
                "tree_id": tree_id,
                "check_fn": behavior_check,
                "token": token,
                "payload": payload,
                "interval_s": interval_s,
                "stop_event": handle.stop_event,
                "on_revoke": on_revoke,
            },
            daemon=True,
            name=f"watcher-beh-{tree_id[:8]}",
        )
        handle.threads.append(beh_thread)

    for thread in handle.threads:
        thread.start()
    return handle
