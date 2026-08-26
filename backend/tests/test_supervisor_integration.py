"""Tests for supervisor integration sequence."""

from __future__ import annotations

import os
import unittest

from app.security.control_plane import reset_control_plane
from app.security.integration import (
    bootstrap_supervisor_session,
    handle_agent_request,
    handle_child_via_parent,
)
from app.security.token import CapabilityViolationError, clear_revocations, is_revoked, issue_child_token
from app.security.token_registry import finalize_issued_token
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
        parent = bootstrap_supervisor_session(["run_static_scan", "issue_child"])
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
        self.assertEqual(result.child_token["execution_tier"], "container")
        self.assertEqual(result.child_token["parent_id"], parent["agent_id"])
        self.assertTrue(
            set(result.child_token["capabilities"]).issubset(set(parent["capabilities"]))
        )

    def test_child_cannot_contact_supervisor(self) -> None:
        parent = bootstrap_supervisor_session(["run_static_scan", "ask_parent", "issue_child"])
        child = finalize_issued_token(
            issue_child_token(parent, ["run_static_scan", "ask_parent"], ttl=60)
        )
        payload = {"action": "run_static_scan", "path": "backend/web_gateway/app.py"}
        result = handle_agent_request(payload, child)
        self.assertEqual(result.verdict, "BLOCK")
        self.assertIn("route through parent", result.reason.lower())

    def test_child_via_parent_ask_parent(self) -> None:
        parent = bootstrap_supervisor_session(["ask_parent", "issue_child"])
        child = finalize_issued_token(
            issue_child_token(parent, ["ask_parent"], ttl=60)
        )
        result = handle_child_via_parent({"action": "ask_parent"}, child, parent)
        self.assertEqual(result.verdict, "PASS")
        self.assertEqual(child.get("execution_tier"), "container")
        self.assertEqual(child.get("parent_id"), parent["agent_id"])

    def test_child_cannot_issue_child(self) -> None:
        parent = bootstrap_supervisor_session(["run_static_scan", "issue_child"])
        child = finalize_issued_token(issue_child_token(parent, ["run_static_scan"], ttl=60))
        with self.assertRaises(CapabilityViolationError):
            issue_child_token(child, ["run_static_scan"])
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
