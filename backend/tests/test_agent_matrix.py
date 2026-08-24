from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("HERMES_SUPERVISOR_HMAC_KEY", "a" * 48)
os.environ.setdefault("CLAW_URL", "http://127.0.0.1:9000")
os.environ.setdefault("HERMES_HOME", tempfile.mkdtemp(prefix="hermes-test-"))
os.environ.setdefault("HERMES_BIND_TAILSCALE", "0")
os.environ.setdefault("HERMES_BIND_HOST", "127.0.0.1")

from wsl_backend.agents.base import AgentRole
from wsl_backend.agents.matrix import ROLE_FACTORIES, agent_class_for
from wsl_backend.agents.registry import AgentRegistry
from wsl_backend.routes_agents import _claw_listening
from wsl_backend.tailscale_net import detect_tailscale_ipv4, resolve_bind_host


class AgentRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = AgentRegistry()

    def test_seed_defaults_covers_roles(self) -> None:
        roles = {a["role"] for a in self.reg.list_public()}
        self.assertEqual(roles, {r.value for r in AgentRole})

    def test_factories_cover_every_role(self) -> None:
        for role in AgentRole:
            self.assertIn(role, ROLE_FACTORIES)
            self.assertIs(agent_class_for(role), ROLE_FACTORIES[role])

    def test_create_and_delete_specialist(self) -> None:
        created = self.reg.create("codex", name="Codex Extra")
        self.assertEqual(created["role"], "codex")
        self.assertTrue(self.reg.delete(created["id"]))
        self.assertIsNone(self.reg.get(created["id"]))

    def test_cannot_delete_last_hermes_or_claw(self) -> None:
        hermes = next(a for a in self.reg.list_public() if a["role"] == "hermes")
        claw = next(a for a in self.reg.list_public() if a["role"] == "claw_opus")
        with self.assertRaises(PermissionError):
            self.reg.delete(hermes["id"])
        with self.assertRaises(PermissionError):
            self.reg.delete(claw["id"])

    def test_cannot_create_extra_claw(self) -> None:
        with self.assertRaises(PermissionError):
            self.reg.create("claw_opus", name="Claw Clone")

    def test_specialist_plan_does_not_execute(self) -> None:
        grok = next(a for a in self.reg.list_public() if a["role"] == "grok")
        result = self.reg.route(grok["id"], "extract citations")
        self.assertTrue(result.ok)
        self.assertEqual(result.kind, "research_plan")
        self.assertTrue(result.route_to_claw)
        self.assertNotIn("claw_text", result.payload)

    def test_memory_fail_closed_without_backends(self) -> None:
        with patch.dict(os.environ, {"REDIS_URL": "", "VECTOR_DB_URL": ""}, clear=False):
            ephemeral = next(a for a in self.reg.list_public() if a["role"] == "memory_ephemeral")
            semantic = next(a for a in self.reg.list_public() if a["role"] == "memory_semantic")
            e_result = self.reg.route(ephemeral["id"], "get session")
            s_result = self.reg.route(semantic["id"], "search notes")
        self.assertFalse(e_result.ok)
        self.assertEqual(e_result.error, "REDIS_URL not configured")
        self.assertFalse(s_result.ok)
        self.assertEqual(s_result.error, "VECTOR_DB_URL not configured")

    def test_claw_handle_does_not_invent_text(self) -> None:
        claw = next(a for a in self.reg.list_public() if a["role"] == "claw_opus")
        result = self.reg.route(claw["id"], "do the work")
        self.assertTrue(result.route_to_claw)
        self.assertNotIn("reply", result.payload)
        self.assertIn("Hermes must call", result.payload.get("note", ""))

    def test_unknown_role(self) -> None:
        with self.assertRaises(KeyError):
            self.reg.create("ollama")

    def test_route_missing_agent(self) -> None:
        result = self.reg.route("missing", "task")
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "agent not found")

    def test_claw_not_listening_when_docker_has_no_claw(self) -> None:
        self.assertFalse(_claw_listening([], docker_ok=True))
        self.assertTrue(_claw_listening(["claw-opus"], docker_ok=True))


class TailscaleBindTests(unittest.TestCase):
    def test_env_ts_ip(self) -> None:
        with patch.dict(os.environ, {"TS_IP": "100.64.1.2"}, clear=False):
            self.assertEqual(detect_tailscale_ipv4(), "100.64.1.2")

    def test_hermes_bind_host_wins(self) -> None:
        with patch.dict(os.environ, {"HERMES_BIND_HOST": "127.0.0.1", "HERMES_BIND_TAILSCALE": "1"}, clear=False):
            self.assertEqual(resolve_bind_host(), "127.0.0.1")

    def test_subprocess_arg_list_not_shell(self) -> None:
        fake = subprocess.CompletedProcess(
            args=["tailscale", "ip", "-4"], returncode=0, stdout="100.64.9.9\n", stderr=""
        )
        with patch.dict(os.environ, {"TS_IP": "", "TAILSCALE_IP": ""}, clear=False):
            with patch("wsl_backend.tailscale_net.shutil.which", return_value="/usr/bin/tailscale"):
                with patch("wsl_backend.tailscale_net.subprocess.run", return_value=fake) as run:
                    ip = detect_tailscale_ipv4()
        self.assertEqual(ip, "100.64.9.9")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["/usr/bin/tailscale", "ip", "-4"])
        self.assertFalse(kwargs.get("shell"))

    def test_missing_tailscale_fail_closed(self) -> None:
        env = {
            "HERMES_BIND_HOST": "",
            "HERMES_BIND_TAILSCALE": "1",
            "HERMES_BIND_ALL": "0",
            "TS_IP": "",
            "TAILSCALE_IP": "",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("wsl_backend.tailscale_net.detect_tailscale_ipv4", return_value=None):
                with self.assertRaises(RuntimeError):
                    resolve_bind_host()

    def test_bind_all_allowed_for_docker(self) -> None:
        env = {
            "HERMES_BIND_HOST": "",
            "HERMES_BIND_TAILSCALE": "1",
            "HERMES_BIND_ALL": "1",
            "TS_IP": "",
            "TAILSCALE_IP": "",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("wsl_backend.tailscale_net.detect_tailscale_ipv4", return_value=None):
                self.assertEqual(resolve_bind_host(), "0.0.0.0")


class StudioHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient
        from wsl_backend.main import create_studio_app

        cls.client = TestClient(create_studio_app())

    def test_list_agents(self) -> None:
        response = self.client.get("/agents")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        roles = {agent["role"] for agent in payload["agents"]}
        self.assertEqual(roles, {r.value for r in AgentRole})

    def test_system_status_shape(self) -> None:
        response = self.client.get("/system/status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("agents", payload)
        self.assertIn("ports", payload)
        self.assertIn("containers", payload)
        self.assertEqual(payload["ports"]["hermes"], 8000)
        self.assertEqual(payload["ports"]["claw"], 9000)

    def test_create_and_delete_via_http(self) -> None:
        created = self.client.post("/agents", json={"role": "codex", "name": "Codex HTTP"})
        self.assertEqual(created.status_code, 200)
        agent_id = created.json()["agent"]["id"]
        routed = self.client.post(f"/agents/{agent_id}/route", json={"task": "sketch a patch"})
        self.assertEqual(routed.status_code, 200)
        self.assertTrue(routed.json()["result"]["route_to_claw"])
        deleted = self.client.delete(f"/agents/{agent_id}")
        self.assertEqual(deleted.status_code, 200)

    def test_studio_health(self) -> None:
        response = self.client.get("/studio/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["agent_worker"], "claw-opus")


class LayoutGuardTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[2]

    def test_no_numbered_v2_folders(self) -> None:
        forbidden = (
            "01_Supervisor_Agent",
            "02_VersionEvaluator",
            "03_Auto_Debugger",
            "04_Ghost_Scraper",
            "05_Local_Database",
            "06_MechIQ_AutoRepair",
            "08_Cloud_K8s",
        )
        for name in forbidden:
            self.assertFalse((self.root / name).exists(), f"legacy folder present: {name}")

    def test_compose_is_memory_backends_only(self) -> None:
        text = (self.root / "docker-compose.yml").read_text(encoding="utf-8").lower()
        self.assertNotIn("ollama", text)
        self.assertNotIn("langgraph", text)
        self.assertIn("redis", text)
        self.assertIn("qdrant", text)
        self.assertNotIn("build: ./services/", text)


if __name__ == "__main__":
    unittest.main()
