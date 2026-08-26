"""Map CI.md session lifecycle to Vultr API v1 calls (manual-aligned)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from infra.vultr.client import VultrClient

WipeHook = Callable[[str], None]


@dataclass
class ConfigurationRecord:
    """Immutable deployment snapshot for rollback (Infrastructure Hub Configurations)."""

    config_id: str
    parent_config_id: str | None
    subid: str
    snapshot_id: str
    description: str
    created_at: str
    sealed_from_baseline: bool = False

    def to_audit_payload(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "parent_config_id": self.parent_config_id,
            "subid": self.subid,
            "snapshot_id": self.snapshot_id,
            "sealed_from_baseline": self.sealed_from_baseline,
        }


class VultrSessionLifecycle:
    """
    CI.md lifecycle expressed through Vultr API v1 (official manual).

    [IMAGE STORED]  → snapshot/list or known SNAPSHOTID
    BOOT            → server/create (OSID 164 + SNAPSHOTID) or server/start
    ACTIVE          → agent_runner.sh on host (Docker — not a Vultr API call)
    TERMINATE       → wipe (optional hook) → halt → restore baseline snapshot
    ROLLBACK        → server/restore_snapshot

    Never snapshot a live session disk — server_halt() preserves contents and
    snapshot_create() would seal sensitive runtime data into a recoverable image.
    """

    def __init__(self, client: VultrClient) -> None:
        self.client = client
        self._config_chain: list[ConfigurationRecord] = []
        self._baseline_by_subid: dict[str, str] = {}

    def list_stored_images(self) -> dict[str, Any]:
        """[IMAGE STORED] — list snapshots on account."""
        return self.client.snapshot_list()

    def boot_from_snapshot(
        self,
        *,
        dcid: int,
        vpsplanid: int,
        snapshot_id: str,
        label: str,
        firewall_group_id: str | None = None,
        script_id: int | None = None,
        parent_config_id: str | None = None,
    ) -> tuple[str, ConfigurationRecord]:
        """
        BOOT triggered — deploy VM from governance-locked snapshot.
        Manual: OSID 164 + SNAPSHOTID on /v1/server/create.
        """
        result = self.client.server_create_from_snapshot(
            dcid=dcid,
            vpsplanid=vpsplanid,
            snapshot_id=snapshot_id,
            label=label,
            firewall_group_id=firewall_group_id,
            script_id=script_id,
        )
        subid = str(result["SUBID"])
        self.client.wait_server_active(subid)
        self._baseline_by_subid[subid] = snapshot_id
        record = ConfigurationRecord(
            config_id=f"cfg_{subid}_{snapshot_id[:8]}",
            parent_config_id=parent_config_id,
            subid=subid,
            snapshot_id=snapshot_id,
            description=f"boot from snapshot {snapshot_id}",
            created_at=datetime.now(timezone.utc).isoformat(),
            sealed_from_baseline=True,
        )
        self._config_chain.append(record)
        return subid, record

    def terminate_and_seal(
        self,
        subid: str,
        *,
        baseline_snapshot_id: str | None = None,
        wipe_hook: WipeHook | None = None,
        description: str | None = None,
    ) -> ConfigurationRecord:
        """
        AUTOMATIC TERMINATION — return VM to the clean baseline image ([IMAGE STORED]).

        CI.md requires runtime state wiped; server_halt() alone keeps disk intact.
        This restores the known-clean baseline snapshot (manual: restore_snapshot —
        all current VM data is lost) instead of snapshot_create() on a dirty disk.

        Call wipe_hook(subid) while the VM is still running to revoke Bitwarden
        sessions, remove local logs, and stop containers before halt/restore.
        """
        baseline = baseline_snapshot_id or self._baseline_by_subid.get(subid)
        if not baseline:
            raise ValueError(
                "baseline_snapshot_id is required — never seal from an unknown session disk. "
                "Pass the governance-locked SNAPSHOTID from boot, or call boot_from_snapshot first."
            )

        if wipe_hook is not None:
            wipe_hook(subid)

        self.client.server_halt(subid)
        self.client.server_restore_snapshot(subid, baseline)
        self.client.wait_server_active(subid)
        self.client.server_halt(subid)

        parent = self._config_chain[-1].config_id if self._config_chain else None
        record = ConfigurationRecord(
            config_id=f"cfg_sealed_{baseline[:8]}_{subid}",
            parent_config_id=parent,
            subid=subid,
            snapshot_id=baseline,
            description=description or f"terminated — restored clean baseline {baseline}",
            created_at=datetime.now(timezone.utc).isoformat(),
            sealed_from_baseline=True,
        )
        self._config_chain.append(record)
        return record

    def rollback(self, subid: str, snapshot_id: str) -> ConfigurationRecord:
        """
        One-click rollback — manual /v1/server/restore_snapshot.
        Any data on VM is lost (manual warning).
        """
        self.client.server_restore_snapshot(subid, snapshot_id)
        self.client.wait_server_active(subid)
        self._baseline_by_subid[subid] = snapshot_id
        parent = self._config_chain[-1].config_id if self._config_chain else None
        record = ConfigurationRecord(
            config_id=f"cfg_rollback_{snapshot_id}",
            parent_config_id=parent,
            subid=subid,
            snapshot_id=snapshot_id,
            description=f"rollback to {snapshot_id}",
            created_at=datetime.now(timezone.utc).isoformat(),
            sealed_from_baseline=True,
        )
        self._config_chain.append(record)
        return record

    @property
    def configuration_history(self) -> list[ConfigurationRecord]:
        return list(self._config_chain)
