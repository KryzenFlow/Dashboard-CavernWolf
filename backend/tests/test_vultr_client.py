"""Tests for Vultr API v1 client (manual-aligned, mocked HTTP)."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from infra.vultr.client import VultrAPIError, VultrClient
from infra.vultr.constants import OSID_SNAPSHOT


class VultrClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = VultrClient(api_key="test-key", min_interval_s=0)

    def test_missing_api_key_raises_403(self) -> None:
        with self.assertRaises(VultrAPIError) as ctx:
            VultrClient(api_key="")
        self.assertEqual(ctx.exception.status, 403)

    @patch("infra.vultr.client.urllib.request.urlopen")
    def test_server_create_from_snapshot_uses_osid_164(self, mock_urlopen: MagicMock) -> None:
        resp = MagicMock()
        resp.read.return_value = json.dumps({"SUBID": "1312965"}).encode()
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        result = self.client.server_create_from_snapshot(
            dcid=1,
            vpsplanid=202,
            snapshot_id="5359435d28b9a",
            label="cavern-wolf",
            firewall_group_id="1234abcd",
        )
        self.assertEqual(result["SUBID"], "1312965")
        req = mock_urlopen.call_args[0][0]
        body = req.data.decode()
        self.assertIn(f"OSID={OSID_SNAPSHOT}", body)
        self.assertIn("SNAPSHOTID=5359435d28b9a", body)
        self.assertIn("FIREWALLGROUPID=1234abcd", body)
        self.assertEqual(req.get_header("Api-key") or req.headers.get("API-key"), "test-key")

    @patch("infra.vultr.client.urllib.request.urlopen")
    def test_restore_snapshot_post(self, mock_urlopen: MagicMock) -> None:
        resp = MagicMock()
        resp.read.return_value = b""
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp

        self.client.server_restore_snapshot("576965", "5359435d28b9a")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.method, "POST")
        self.assertIn("restore_snapshot", req.full_url)
        self.assertIn("SUBID=576965", req.data.decode())
        self.assertIn("SNAPSHOTID=5359435d28b9a", req.data.decode())


if __name__ == "__main__":
    unittest.main()
