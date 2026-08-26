"""
app/security/merkle.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Merkle Root Seal — Audit Ledger
Cavern Wolf v2 | Trust Discipline Framework
Author: Drew | aheaddigitalai
Version: 1.0 | August 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SQL SERVER SCHEMA:
    CREATE TABLE audit_ledger (
        id            BIGINT IDENTITY PRIMARY KEY,
        session_id    NVARCHAR(64)    NOT NULL,
        agent         NVARCHAR(128)   NOT NULL,
        entry_count   INT             NOT NULL,
        merkle_root   NCHAR(64)       NOT NULL,
        sealed_at     DATETIMEOFFSET  NOT NULL,
        entries_json  NVARCHAR(MAX)   NOT NULL,
        verified      BIT             DEFAULT 0
    );
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


# ── Core Hash Primitive ───────────────────────────────────────────────────────

def sha256_hex(data: bytes) -> str:
    """Return SHA-256 digest as a lowercase hex string."""
    return hashlib.sha256(data).hexdigest()


def hash_payload(payload: dict) -> str:
    """Deterministically hash a dict payload. Raw payload is never stored."""
    return sha256_hex(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8"))


# ── Log Entry ─────────────────────────────────────────────────────────────────

@dataclass
class LogEntry:
    timestamp: str
    session_id: str
    agent: str
    action: str
    payload_hash: str
    actor: str
    sequence: int

    def to_canonical_bytes(self) -> bytes:
        canonical = {
            "action": self.action,
            "actor": self.actor,
            "agent": self.agent,
            "payload_hash": self.payload_hash,
            "sequence": self.sequence,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }
        return json.dumps(canonical, sort_keys=True, ensure_ascii=True).encode("utf-8")

    def entry_hash(self) -> str:
        return sha256_hex(self.to_canonical_bytes())

    def to_audit_dict(self) -> dict:
        return {
            "seq": self.sequence,
            "timestamp": self.timestamp,
            "agent": self.agent,
            "action": self.action,
            "actor": self.actor,
            "payload_hash": self.payload_hash,
            "entry_hash": self.entry_hash(),
        }


# ── Merkle Tree ───────────────────────────────────────────────────────────────

class MerkleTree:
    def __init__(self, entries: List[LogEntry]) -> None:
        self.entries = entries
        self.leaf_hashes = [e.entry_hash() for e in entries]
        self.levels: List[List[str]] = []
        self.root = self._build_root(self.leaf_hashes[:])

    def _build_root(self, hashes: List[str]) -> Optional[str]:
        if not hashes:
            return None
        if len(hashes) == 1:
            return hashes[0]
        if len(hashes) % 2 != 0:
            hashes = hashes + [hashes[-1]]
        parent: List[str] = []
        for i in range(0, len(hashes), 2):
            combined = (hashes[i] + hashes[i + 1]).encode("utf-8")
            parent.append(sha256_hex(combined))
        self.levels.append(parent)
        return self._build_root(parent)

    def verify_root(self, expected: str) -> bool:
        return self.root == expected

    @staticmethod
    def recompute_root_from_hashes(leaf_hashes: List[str]) -> Optional[str]:
        if not leaf_hashes:
            return None
        hashes = leaf_hashes[:]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            next_level: List[str] = []
            for i in range(0, len(hashes), 2):
                combined = (hashes[i] + hashes[i + 1]).encode("utf-8")
                next_level.append(sha256_hex(combined))
            hashes = next_level
        return hashes[0]


# ── Audit Ledger ──────────────────────────────────────────────────────────────

class AuditLedger:
    """
    Session-scoped audit ledger for one Cavern Wolf agent lifecycle.

    Usage:
        ledger = AuditLedger.new_session(agent="cavern_wolf_v2")
        ledger.record("TOOL_CALL", {"tool": "search"}, actor="agent")
        root   = ledger.seal()
        record = ledger.to_sql_record()
        # → INSERT INTO audit_ledger ...

        valid  = AuditLedger.verify_sealed_record(sql_row)
    """

    def __init__(self, session_id: str, agent: str) -> None:
        self.session_id = session_id
        self.agent = agent
        self.entries: List[LogEntry] = []
        self._sequence = 0
        self.sealed = False
        self.seal_root: Optional[str] = None
        self.seal_timestamp: Optional[str] = None
        self.previous_root: Optional[str] = None

    @classmethod
    def new_session(cls, agent: str, previous_root: Optional[str] = None) -> "AuditLedger":
        ledger = cls(session_id=str(uuid.uuid4()), agent=agent)
        ledger.previous_root = previous_root
        ledger.record(
            "SESSION_BOOT",
            {
                "agent": agent,
                "previous_root": previous_root,
                "boot_time": datetime.now(timezone.utc).isoformat(),
            },
            actor="system",
        )
        return ledger

    def record(self, action: str, payload: dict, actor: str = "system") -> LogEntry:
        if self.sealed:
            raise RuntimeError(f"[AuditLedger] Session {self.session_id} is sealed.")
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            agent=self.agent,
            action=action,
            payload_hash=hash_payload(payload),
            actor=actor,
            sequence=self._sequence,
        )
        self.entries.append(entry)
        self._sequence += 1
        return entry

    def seal(self) -> str:
        if self.sealed:
            raise RuntimeError(f"[AuditLedger] Already sealed. Root: {self.seal_root}")
        self.record(
            "SESSION_SEAL",
            {
                "entry_count": len(self.entries) + 1,
                "session_id": self.session_id,
                "previous_root": self.previous_root,
            },
            actor="system",
        )
        tree = MerkleTree(self.entries)
        self.seal_root = tree.root
        self.seal_timestamp = datetime.now(timezone.utc).isoformat()
        self.sealed = True
        return self.seal_root

    def to_sql_record(self) -> dict:
        if not self.sealed:
            raise RuntimeError("[AuditLedger] Must seal before generating SQL record.")
        return {
            "session_id": self.session_id,
            "agent": self.agent,
            "entry_count": len(self.entries),
            "merkle_root": self.seal_root,
            "sealed_at": self.seal_timestamp,
            "entries_json": json.dumps([e.to_audit_dict() for e in self.entries], ensure_ascii=True),
            "verified": 0,
        }

    @staticmethod
    def verify_sealed_record(record: dict) -> bool:
        """
        Recomputes every entry hash FROM SCRATCH from stored field values.
        Catches: field tampering, hash substitution, and root substitution.
        Returns True if intact, False if tampered — raise an alert on False.
        """
        try:
            entries_data = json.loads(record["entries_json"])
        except (json.JSONDecodeError, KeyError) as exc:
            raise ValueError(f"[AuditLedger] Cannot parse entries_json: {exc}") from exc

        session_id = record.get("session_id", "")

        if len(entries_data) != record.get("entry_count", -1):
            return False

        for expected_seq, entry in enumerate(entries_data):
            if entry.get("seq") != expected_seq:
                return False

        leaf_hashes: List[str] = []
        for entry in entries_data:
            canonical = {
                "action": entry.get("action", ""),
                "actor": entry.get("actor", ""),
                "agent": entry.get("agent", ""),
                "payload_hash": entry.get("payload_hash", ""),
                "sequence": entry.get("seq", -1),
                "session_id": session_id,
                "timestamp": entry.get("timestamp", ""),
            }
            recomputed = sha256_hex(
                json.dumps(canonical, sort_keys=True, ensure_ascii=True).encode("utf-8")
            )
            if recomputed != entry.get("entry_hash", ""):
                return False
            leaf_hashes.append(recomputed)

        computed_root = MerkleTree.recompute_root_from_hashes(leaf_hashes)
        return computed_root == record.get("merkle_root")

    def summary(self) -> dict:
        return {
            "session_id": self.session_id,
            "agent": self.agent,
            "entry_count": len(self.entries),
            "sealed": self.sealed,
            "merkle_root": self.seal_root or "NOT SEALED",
            "sealed_at": self.seal_timestamp or "NOT SEALED",
            "previous_root": self.previous_root or "NONE (first session)",
        }

    def __repr__(self) -> str:
        status = f"SEALED root={self.seal_root[:12]}..." if self.sealed else "OPEN"
        return (
            f"<AuditLedger session={self.session_id[:8]}... "
            f"agent={self.agent} entries={len(self.entries)} {status}>"
        )


# ── Cavern Wolf Shutdown Hook ─────────────────────────────────────────────────

def terminate_session(ledger: AuditLedger, db_insert_fn) -> str:
    """
    Wire to SIGTERM/SIGINT and your Docker stop signal.
    Seals the ledger, persists to SQL, returns the Merkle root.

    Example:
        import signal, sys
        ledger = AuditLedger.new_session(agent="cavern_wolf_v2")

        def shutdown(signum, frame):
            root = terminate_session(ledger, db_insert_fn=my_db_write)
            print(f"[SEALED] {root}")
            sys.exit(0)

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT,  shutdown)
    """
    ledger.record(
        "TERMINATION_SIGNAL",
        {"agent": ledger.agent, "session_id": ledger.session_id},
        actor="system",
    )
    root = ledger.seal()
    sql_record = ledger.to_sql_record()
    db_insert_fn(sql_record)
    return root


# ── Self-Test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import copy

    print("━" * 68)
    print(" Merkle Root Seal — Self-Test")
    print("━" * 68)

    ledger = AuditLedger.new_session(agent="cavern_wolf_v2")
    print(f"\n[BOOT]  {ledger}")

    ledger.record("CREDENTIAL_INJECT", {"source": "bitwarden", "key_count": 4}, actor="system")
    ledger.record("TOOL_CALL", {"tool": "web_search", "query": "redacted"}, actor="agent")
    ledger.record("OUTPUT_GENERATED", {"output_length": 512, "model": "opus"}, actor="agent")
    ledger.record("ESCALATION", {"reason": "outside_parameters"}, actor="agent")
    print(f"[RUN]   {len(ledger.entries)} entries recorded")

    root = ledger.seal()
    print(f"[SEAL]  Merkle root: {root}")
    sql_record = ledger.to_sql_record()
    print(f"\n[SQL]   entry_count : {sql_record['entry_count']}")
    print(f"[SQL]   merkle_root  : {sql_record['merkle_root']}")
    print(f"[SQL]   sealed_at    : {sql_record['sealed_at']}")

    assert AuditLedger.verify_sealed_record(sql_record), "FAIL: valid record"
    print("\n[VERIFY] Record intact: True")

    tampered = copy.deepcopy(sql_record)
    entries = json.loads(tampered["entries_json"])
    entries[1]["action"] = "TAMPERED_ACTION"
    tampered["entries_json"] = json.dumps(entries)
    assert not AuditLedger.verify_sealed_record(tampered), "FAIL: tamper not detected"
    print("[VERIFY] Tampered record detected: True")

    print("\n" + "━" * 68)
    print(" All self-tests passed. ✓")
    print("━" * 68)
    print(f"\n Summary: {json.dumps(ledger.summary(), indent=2)}")
