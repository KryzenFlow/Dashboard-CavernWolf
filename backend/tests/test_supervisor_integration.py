"""Tests for supervisor integration sequence."""

from __future__ import annotations

import os
import unittest

from app.security.control_plane import reset_control_plane
from app.security.integration import bootstrap_supervisor_session, handle_agent_request
from app.security.token import CapabilityViolationError, clear_revocations, is_revoked, issue_child_token
from app.security.supervisor_gates import validate_and_gate

os.environ.setdefault("HERMES_SUPERVISOR_HMAC_KEY", "a" * 48)


class SupervisorIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_control_plane()
        clear_revocations()

    def test_validate_and_gate_passes_clean_payload(self) -> None:
        parent = bootstrap_supervisor_session(["read_workspace", "run_static_scan"])
        payload = {"action": "run_static_scan", "path": "backend/routes/api.py"}
        verdict, reason = validate_and_gate(payload, parent, action="run_static_scan")
        self.assertEqual(verdict, "PASS")
        self.assertIn("cleared", reason)

    def test_path_traversal_blocks(self) -> None:
        parent = bootstrap_supervisor_session(["read_workspace"])
        payload = {"action": "read_workspace", "path": "../etc/passwd"}
        verdict, reason = validate_and_gate(payload, parent, action="read_workspace")
        self.assertEqual(verdict, "BLOCK")
        self.assertIn("Path confinement", reason)

    def test_child_capability_attenuation(self) -> None:
        parent = bootstrap_supervisor_session(["read_workspace"])
        with self.assertRaises(CapabilityViolationError):
            issue_child_token(parent, ["orch:ask_hermes"])

    def test_handle_agent_request_revokes_on_block(self) -> None:
        parent = bootstrap_supervisor_session(["read_workspace"])
        tree_id = parent["tree_id"]
        payload = {"action": "read_workspace", "cmd": "rm -rf /"}
        result = handle_agent_request(payload, parent)
        self.assertEqual(result.verdict, "BLOCK")
        self.assertTrue(is_revoked(tree_id))

    def test_handle_agent_request_issues_child_on_pass(self) -> None:
        parent = bootstrap_supervisor_session(["run_static_scan"])
        payload = {"action": "run_static_scan", "path": "backend/web_gateway/app.py"}
        result = handle_agent_request(
            payload,
            parent,
            child_capabilities=["run_static_scan"],
            child_ttl=60,
        )
        self.assertEqual(result.verdict, "PASS")
        self.assertIsNotNone(result.child_token)
        assert result.child_token is not None
        self.assertTrue(
            set(result.child_token["capabilities"]).issubset(set(parent["capabilities"]))
        )


if __name__ == "__main__":
    unittest.main()
