from __future__ import annotations

import os
import unittest

os.environ["HERMES_SUPERVISOR_HMAC_KEY"] = "a" * 48
os.environ["CLAW_URL"] = "http://127.0.0.1:9000"
os.environ.pop("HERMES_MOCK", None)

from web_gateway.security.environment import FalseEnvironment, assert_no_false_environment, require_real_env
from web_gateway.security.merkle import compute_merkle_root, inclusion_proof, verify_inclusion
from web_gateway.security.token import SecurityError, issue_child_token, issue_token, validate_token


class MerkleAuthTests(unittest.TestCase):
    def test_inclusion_roundtrip(self) -> None:
        leaves = ["a", "b", "c"]
        root = compute_merkle_root(leaves)
        proof = inclusion_proof(leaves, 1)
        self.assertTrue(verify_inclusion("b", proof, root))
        self.assertFalse(verify_inclusion("nope", proof, root))
        self.assertEqual(compute_merkle_root([]), "")

    def test_child_cannot_escalate(self) -> None:
        parent = issue_token(
            tree_id="t1",
            agent_id="p1",
            capabilities=["tool:grant_child", "tool:ask_parent", "orch:ask_hermes"],
            ttl_seconds=60,
            merkle_root="abc",
            role="parent",
        )
        child = issue_child_token(parent, ["tool:ask_parent"], ttl=30)
        self.assertEqual(child["parent_id"], "p1")
        self.assertEqual(child["role"], "child")
        ok, _ = validate_token(child)
        self.assertTrue(ok)
        with self.assertRaises(SecurityError):
            issue_child_token(parent, ["orch:ask_hermes"], ttl=30)

    def test_false_environment_rejected(self) -> None:
        old = os.environ["HERMES_SUPERVISOR_HMAC_KEY"]
        os.environ["HERMES_SUPERVISOR_HMAC_KEY"] = "dev-change-me"
        with self.assertRaises(FalseEnvironment):
            require_real_env("HERMES_SUPERVISOR_HMAC_KEY")
        os.environ["HERMES_SUPERVISOR_HMAC_KEY"] = old
        os.environ["HERMES_MOCK"] = "1"
        with self.assertRaises(FalseEnvironment):
            assert_no_false_environment()
        del os.environ["HERMES_MOCK"]


if __name__ == "__main__":
    unittest.main()
