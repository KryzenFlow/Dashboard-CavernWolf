"""Vultr API v1 client — aligned with Vultr API Reference v1.0 (2020-09-11).

Authentication: API-Key header (manual Overview).
Endpoint base: https://api.vultr.com/
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from infra.vultr.constants import (
    API_BASE,
    HTTP_OK,
    HTTP_RATE_LIMIT,
    OSID_SNAPSHOT,
    VULTR_HTTP_MESSAGES,
)


class VultrAPIError(RuntimeError):
    def __init__(self, status: int, message: str, body: str = "") -> None:
        self.status = status
        self.body = body
        super().__init__(f"Vultr API {status}: {message}" + (f" — {body[:200]}" if body else ""))


class VultrClient:
    """
    Thin wrapper over Vultr API v1 per the official manual.
    API key from VULTR_API_KEY env or constructor — never log the key.
    """

    def __init__(self, api_key: str | None = None, *, min_interval_s: float = 0.55) -> None:
        key = (api_key or os.environ.get("VULTR_API_KEY", "")).strip()
        if not key:
            raise VultrAPIError(403, "Invalid or missing API key", "Set VULTR_API_KEY")
        self._api_key = key
        self._min_interval_s = min_interval_s
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval_s:
            time.sleep(self._min_interval_s - elapsed)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        auth_required: bool = True,
    ) -> Any:
        self._throttle()
        url = f"{API_BASE}/{path.lstrip('/')}"
        headers = {"Accept": "application/json"}
        if auth_required:
            headers["API-Key"] = self._api_key

        body_bytes: bytes | None = None
        if method.upper() == "GET" and params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"
        elif method.upper() == "POST" and data is not None:
            body_bytes = urllib.parse.urlencode(
                {k: v for k, v in data.items() if v is not None}
            ).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=body_bytes, method=method.upper(), headers=headers)
        self._last_request_at = time.monotonic()

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                if not raw.strip():
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            msg = VULTR_HTTP_MESSAGES.get(exc.code, err_body or exc.reason)
            if exc.code == HTTP_RATE_LIMIT:
                msg = VULTR_HTTP_MESSAGES[HTTP_RATE_LIMIT]
            raise VultrAPIError(exc.code, msg, err_body) from exc

    # ── Account / auth (manual) ─────────────────────────────────────────────

    def account_info(self) -> dict[str, Any]:
        return self._request("GET", "v1/account/info")

    def auth_info(self) -> dict[str, Any]:
        return self._request("GET", "v1/auth/info")

    # ── Server (manual) ─────────────────────────────────────────────────────

    def server_list(self, **filters: Any) -> dict[str, Any]:
        """GET /v1/server/list — optional SUBID, tag, label, main_ip filters."""
        return self._request("GET", "v1/server/list", params=filters or None)

    def server_get(self, subid: int | str) -> dict[str, Any] | None:
        result = self.server_list(SUBID=subid)
        return result.get(str(subid)) if isinstance(result, dict) else None

    def server_create(self, **params: Any) -> dict[str, Any]:
        """POST /v1/server/create — returns {\"SUBID\": \"...\"}."""
        return self._request("POST", "v1/server/create", data=params)

    def server_create_from_snapshot(
        self,
        *,
        dcid: int,
        vpsplanid: int,
        snapshot_id: str,
        label: str | None = None,
        firewall_group_id: str | None = None,
        script_id: int | None = None,
        sshkey_id: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Manual: OSID 164 + SNAPSHOTID to deploy from snapshot ([IMAGE STORED])."""
        payload: dict[str, Any] = {
            "DCID": dcid,
            "VPSPLANID": vpsplanid,
            "OSID": OSID_SNAPSHOT,
            "SNAPSHOTID": snapshot_id,
        }
        if label:
            payload["label"] = label
        if firewall_group_id:
            payload["FIREWALLGROUPID"] = firewall_group_id
        if script_id is not None:
            payload["SCRIPTID"] = script_id
        if sshkey_id:
            payload["SSHKEYID"] = sshkey_id
        payload.update(extra)
        return self.server_create(**payload)

    def server_halt(self, subid: int | str) -> None:
        """POST /v1/server/halt — hard power off (session terminate, data preserved on disk)."""
        self._request("POST", "v1/server/halt", data={"SUBID": subid})

    def server_start(self, subid: int | str) -> None:
        self._request("POST", "v1/server/start", data={"SUBID": subid})

    def server_reboot(self, subid: int | str) -> None:
        self._request("POST", "v1/server/reboot", data={"SUBID": subid})

    def server_destroy(self, subid: int | str) -> None:
        self._request("POST", "v1/server/destroy", data={"SUBID": subid})

    def server_bandwidth(self, subid: int | str, *, date_range: int | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"SUBID": subid}
        if date_range is not None:
            params["date_range"] = date_range
        return self._request("GET", "v1/server/bandwidth", params=params)

    def server_restore_snapshot(self, subid: int | str, snapshot_id: str) -> None:
        """POST /v1/server/restore_snapshot — rollback; existing VM data lost."""
        self._request(
            "POST",
            "v1/server/restore_snapshot",
            data={"SUBID": subid, "SNAPSHOTID": snapshot_id},
        )

    def server_firewall_group_set(self, subid: int | str, firewall_group_id: str) -> None:
        self._request(
            "POST",
            "v1/server/firewall_group_set",
            data={"SUBID": subid, "FIREWALLGROUPID": firewall_group_id},
        )

    def wait_server_active(
        self,
        subid: int | str,
        *,
        timeout_s: float = 600,
        poll_s: float = 10,
    ) -> dict[str, Any]:
        """Manual: poll server/list until status=active and server_state=ok."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            server = self.server_get(subid)
            if server and server.get("status") == "active" and server.get("server_state") == "ok":
                return server
            time.sleep(poll_s)
        raise TimeoutError(f"SUBID {subid} not active within {timeout_s}s")

    # ── Snapshot (manual) ───────────────────────────────────────────────────

    def snapshot_list(self, snapshot_id: str | None = None) -> dict[str, Any]:
        params = {"SNAPSHOTID": snapshot_id} if snapshot_id else None
        return self._request("GET", "v1/snapshot/list", params=params)

    def snapshot_create(self, subid: int | str, *, description: str | None = None) -> dict[str, Any]:
        """POST /v1/snapshot/create — seal [IMAGE STORED] after session."""
        data: dict[str, Any] = {"SUBID": subid}
        if description:
            data["description"] = description
        return self._request("POST", "v1/snapshot/create", data=data)

    def snapshot_destroy(self, snapshot_id: str) -> None:
        self._request("POST", "v1/snapshot/destroy", data={"SNAPSHOTID": snapshot_id})

    # ── Firewall (manual) ───────────────────────────────────────────────────

    def firewall_group_list(self, firewall_group_id: str | None = None) -> dict[str, Any]:
        params = {"FIREWALLGROUPID": firewall_group_id} if firewall_group_id else None
        return self._request("GET", "v1/firewall/group_list", params=params)

    def firewall_group_create(self, *, description: str | None = None) -> dict[str, Any]:
        data = {"description": description} if description else {}
        return self._request("POST", "v1/firewall/group_create", data=data)

    def firewall_rule_create(
        self,
        *,
        firewall_group_id: str,
        direction: str = "in",
        ip_type: str = "v4",
        protocol: str = "tcp",
        subnet: str,
        subnet_size: int,
        port: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "FIREWALLGROUPID": firewall_group_id,
            "direction": direction,
            "ip_type": ip_type,
            "protocol": protocol,
            "subnet": subnet,
            "subnet_size": subnet_size,
        }
        if port:
            data["port"] = port
        if notes:
            data["notes"] = notes
        return self._request("POST", "v1/firewall/rule_create", data=data)

    def firewall_rule_list(
        self,
        firewall_group_id: str,
        *,
        direction: str | None = None,
        ip_type: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"FIREWALLGROUPID": firewall_group_id}
        if direction:
            params["direction"] = direction
        if ip_type:
            params["ip_type"] = ip_type
        return self._request("GET", "v1/firewall/rule_list", params=params)

    # ── Startup script (manual) ─────────────────────────────────────────────

    def startupscript_create(self, *, name: str, script: str, script_type: str = "boot") -> dict[str, Any]:
        return self._request(
            "POST",
            "v1/startupscript/create",
            data={"name": name, "script": script, "type": script_type},
        )

    def startupscript_list(self) -> dict[str, Any]:
        return self._request("GET", "v1/startupscript/list")

    # ── Regions / plans (manual helpers) ────────────────────────────────────

    def regions_list(self) -> dict[str, Any]:
        return self._request("GET", "v1/regions/list", auth_required=False)

    def plans_list(self) -> dict[str, Any]:
        return self._request("GET", "v1/plans/list", auth_required=False)

    def os_list(self) -> dict[str, Any]:
        return self._request("GET", "v1/os/list", auth_required=False)
