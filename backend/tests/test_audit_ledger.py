"""Tests for app.security.merkle audit ledger."""

from __future__ import annotations

import copy
import json
import unittest

from app.security.merkle import AuditLedger, MerkleTree, hash_payload, sha256_hex


class AuditLedgerTests(unittest.TestCase):
    def test_hash_payload_deterministic(self) -> None:
        payload = {"tool": "search", "query": "test"}
        self.assertEqual(hash_payload(payload), hash_payload(payload))
        self.assertEqual(len(hash_payload(payload)), 64)

    def test_merkle_root_odd_leaf_count(self) -> None:
        leaves = ["aaa", "bbb", "ccc"]
        root = MerkleTree.recompute_root_from_hashes(leaves)
        self.assertIsNotNone(root)
        self.assertEqual(len(root or ""), 64)

    def test_session_seal_and_verify(self) -> None:
        ledger = AuditLedger.new_session(agent="cavern_wolf_v2")
        ledger.record("TOOL_CALL", {"tool": "web_search"}, actor="agent")
        ledger.seal()
        record = ledger.to_sql_record()
        self.assertTrue(AuditLedger.verify_sealed_record(record))
        self.assertEqual(record["entry_count"], len(json.loads(record["entries_json"])))

    def test_tamper_detection(self) -> None:
        ledger = AuditLedger.new_session(agent="cavern_wolf_v2")
        ledger.record("TOOL_CALL", {"tool": "web_search"}, actor="agent")
        ledger.seal()
        tampered = copy.deepcopy(ledger.to_sql_record())
        entries = json.loads(tampered["entries_json"])
        entries[1]["action"] = "TAMPERED"
        tampered["entries_json"] = json.dumps(entries)
        self.assertFalse(AuditLedger.verify_sealed_record(tampered))

    def test_sealed_session_rejects_record(self) -> None:
        ledger = AuditLedger.new_session(agent="cavern_wolf_v2")
        ledger.seal()
        with self.assertRaises(RuntimeError):
            ledger.record("LATE_ENTRY", {}, actor="agent")

    def test_previous_root_chain(self) -> None:
        first = AuditLedger.new_session(agent="cavern_wolf_v2")
        first_root = first.seal()
        second = AuditLedger.new_session(agent="cavern_wolf_v2", previous_root=first_root)
        self.assertEqual(second.previous_root, first_root)
        boot_entries = [e for e in second.entries if e.action == "SESSION_BOOT"]
        self.assertEqual(len(boot_entries), 1)

    def test_terminate_session_persists(self) -> None:
        ledger = AuditLedger.new_session(agent="cavern_wolf_v2")
        stored: list[dict] = []

        def db_insert(record: dict) -> None:
            stored.append(record)

        from app.security.merkle import terminate_session

        root = terminate_session(ledger, db_insert)
        self.assertEqual(len(stored), 1)
        self.assertTrue(AuditLedger.verify_sealed_record(stored[0]))
        self.assertEqual(stored[0]["merkle_root"], root)


class Sha256Tests(unittest.TestCase):
    def test_sha256_hex(self) -> None:
        self.assertEqual(
            sha256_hex(b"test"),
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        )


if __name__ == "__main__":
    unittest.main()
