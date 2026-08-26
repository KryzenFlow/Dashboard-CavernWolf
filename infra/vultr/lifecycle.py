"""Map CI.md session lifecycle to Vultr API v1 calls (manual-aligned)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from infra.vultr.client import VultrClient


@dataclass
class ConfigurationRecord:
    """Immutable deployment snapshot for rollback (Infrastructure Hub Configurations)."""

    config_id: str
    parent_config_id: str | None
    subid: str
    snapshot_id: str
    description: str
    created_at: str

    def to_audit_payload(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "parent_config_id": self.parent_config_id,
            "subid": self.subid,
            "snapshot_id": self.snapshot_id,
        }


class VultrSessionLifecycle:
    """
    CI.md lifecycle expressed through Vultr API v1 (official manual).

    [IMAGE STORED]  → snapshot/list or known SNAPSHOTID
    BOOT            → server/create (OSID 164 + SNAPSHOTID) or server/start
    ACTIVE          → agent_runner.sh on host (Docker — not a Vultr API call)
    TERMINATE       → server/halt + snapshot/create (new [IMAGE STORED])
    ROLLBACK        → server/restore_snapshot
    """

    def __init__(self, client: VultrClient) -> None:
        self.client = client
        self._config_chain: list[ConfigurationRecord] = []

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
        record = ConfigurationRecord(
            config_id=f"cfg_{subid}_{snapshot_id[:8]}",
            parent_config_id=parent_config_id,
            subid=subid,
            snapshot_id=snapshot_id,
            description=f"boot from snapshot {snapshot_id}",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._config_chain.append(record)
        return subid, record

    def terminate_and_seal(
        self,
        subid: str,
        *,
        description: str | None = None,
    ) -> ConfigurationRecord:
        """
        AUTOMATIC TERMINATION — halt VM, snapshot disk state ([IMAGE STORED]).
        Matches CI.md: lifecycle cut, image ready for next return.
        """
        self.client.server_halt(subid)
        snap = self.client.snapshot_create(
            subid,
            description=description or f"sealed {datetime.now(timezone.utc).isoformat()}",
        )
        snapshot_id = str(snap["SNAPSHOTID"])
        parent = self._config_chain[-1].config_id if self._config_chain else None
        record = ConfigurationRecord(
            config_id=f"cfg_sealed_{snapshot_id}",
            parent_config_id=parent,
            subid=subid,
            snapshot_id=snapshot_id,
            description=description or "session sealed snapshot",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._config_chain.append(record)
        return record

    def rollback(self, subid: str, snapshot_id: str) -> ConfigurationRecord:
        """
        One-click rollback — manual /v1/server/restore_snapshot.
        Any data on VM is lost (manual warning).
        """
        self.client.server_restore_snapshot(subid, snapshot_id)
        parent = self._config_chain[-1].config_id if self._config_chain else None
        record = ConfigurationRecord(
            config_id=f"cfg_rollback_{snapshot_id}",
            parent_config_id=parent,
            subid=subid,
            snapshot_id=snapshot_id,
            description=f"rollback to {snapshot_id}",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._config_chain.append(record)
        return record

    @property
    def configuration_history(self) -> list[ConfigurationRecord]:
        return list(self._config_chain)
