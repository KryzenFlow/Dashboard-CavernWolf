"""Dual independent watchers — scoped revoke without killing unaffected agents."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.security.hierarchy import is_child_token
from app.security.token import (
    extract_agent_id,
    extract_tree_id,
    is_agent_revoked,
    is_revoked,
    revoke_agent,
    revoke_tree,
    validate_token,
)

WatcherFn = Callable[[dict[str, Any], dict[str, Any]], str | None]
RevokeFn = Callable[[dict[str, Any], str], None]


@dataclass
class WatcherHandle:
    tree_id: str
    agent_id: str
    stop_event: threading.Event = field(default_factory=threading.Event)
    threads: list[threading.Thread] = field(default_factory=list)

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=2.0)


def _scoped_revoke(token: dict[str, Any], reason: str) -> None:
    """Child watchers kill the child only; parent watchers kill the tree."""
    tree_id = extract_tree_id(token) or ""
    agent_id = extract_agent_id(token) or ""
    if is_child_token(token):
        if agent_id:
            revoke_agent(agent_id, reason=reason)
    elif tree_id:
        revoke_tree(tree_id, reason=reason)


def _is_scoped_revoked(token: dict[str, Any]) -> bool:
    tree_id = extract_tree_id(token) or ""
    agent_id = extract_agent_id(token) or ""
    if is_child_token(token):
        return is_agent_revoked(agent_id) or is_revoked(tree_id)
    return is_revoked(tree_id)


def _capability_watcher(
    *,
    token: dict[str, Any],
    payload: dict[str, Any],
    interval_s: float,
    stop_event: threading.Event,
    on_revoke: RevokeFn | None,
) -> None:
    while not stop_event.is_set():
        if _is_scoped_revoked(token):
            return
        ok, reason = validate_token(token)
        if not ok:
            revoke_reason = f"capability watcher: {reason}"
            _scoped_revoke(token, revoke_reason)
            if on_revoke:
                on_revoke(token, revoke_reason)
            return
        time.sleep(interval_s)


def _behavior_watcher(
    *,
    check_fn: WatcherFn,
    token: dict[str, Any],
    payload: dict[str, Any],
    interval_s: float,
    stop_event: threading.Event,
    on_revoke: RevokeFn | None,
) -> None:
    while not stop_event.is_set():
        if _is_scoped_revoked(token):
            return
        reason = check_fn(token, payload)
        if reason:
            revoke_reason = f"behavior watcher: {reason}"
            _scoped_revoke(token, revoke_reason)
            if on_revoke:
                on_revoke(token, revoke_reason)
            return
        time.sleep(interval_s)


def start_dual_watchers(
    token: dict[str, Any],
    payload: dict[str, Any],
    *,
    behavior_check: WatcherFn | None = None,
    interval_s: float = 0.5,
    on_revoke: RevokeFn | None = None,
) -> WatcherHandle:
    """
    Side 1 — behavioral/process policy hook.
    Side 2 — capability/token re-validation.
    Child tokens → revoke_agent only. Parent tokens → revoke_tree on severe watcher trip.
    """
    tree_id = extract_tree_id(token) or ""
    agent_id = extract_agent_id(token) or ""
    handle = WatcherHandle(tree_id=tree_id, agent_id=agent_id)

    cap_thread = threading.Thread(
        target=_capability_watcher,
        kwargs={
            "token": token,
            "payload": payload,
            "interval_s": interval_s,
            "stop_event": handle.stop_event,
            "on_revoke": on_revoke,
        },
        daemon=True,
        name=f"watcher-cap-{agent_id[:8] or tree_id[:8]}",
    )
    handle.threads.append(cap_thread)

    if behavior_check is not None:
        beh_thread = threading.Thread(
            target=_behavior_watcher,
            kwargs={
                "check_fn": behavior_check,
                "token": token,
                "payload": payload,
                "interval_s": interval_s,
                "stop_event": handle.stop_event,
                "on_revoke": on_revoke,
            },
            daemon=True,
            name=f"watcher-beh-{agent_id[:8] or tree_id[:8]}",
        )
        handle.threads.append(beh_thread)

    for thread in handle.threads:
        thread.start()
    return handle
