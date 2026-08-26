"""Tests for Vultr session lifecycle — terminate must not snapshot dirty disks."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from infra.vultr.lifecycle import VultrSessionLifecycle


class VultrLifecycleTerminateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = MagicMock()
        self.client.wait_server_active.return_value = {"status": "active", "server_state": "ok"}
        self.lifecycle = VultrSessionLifecycle(self.client)

    def test_terminate_restores_baseline_never_snapshots_session_disk(self) -> None:
        wiped: list[str] = []

        def wipe(subid: str) -> None:
            wiped.append(subid)

        record = self.lifecycle.terminate_and_seal(
            "576965",
            baseline_snapshot_id="5359435d28b9a",
            wipe_hook=wipe,
        )

        self.assertEqual(wiped, ["576965"])
        self.client.server_halt.assert_any_call("576965")
        self.client.server_restore_snapshot.assert_called_once_with("576965", "5359435d28b9a")
        self.client.snapshot_create.assert_not_called()
        self.assertEqual(record.snapshot_id, "5359435d28b9a")
        self.assertTrue(record.sealed_from_baseline)

    def test_terminate_uses_baseline_from_boot(self) -> None:
        self.lifecycle._baseline_by_subid["999"] = "abc123456789"

        record = self.lifecycle.terminate_and_seal("999")

        self.client.server_restore_snapshot.assert_called_once_with("999", "abc123456789")
        self.client.snapshot_create.assert_not_called()
        self.assertEqual(record.snapshot_id, "abc123456789")

    def test_terminate_requires_baseline(self) -> None:
        with self.assertRaises(ValueError):
            self.lifecycle.terminate_and_seal("576965")


if __name__ == "__main__":
    unittest.main()
