"""Tests for infra/secure-agent log redaction."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infra" / "secure-agent"))

from redact_logs import redact_file  # noqa: E402


class RedactLogsTests(unittest.TestCase):
    def test_redacts_password_and_api_key(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".log", delete=False) as tmp:
            tmp.write("password=supersecret\napi_key=abc123\nok line\n")
            tmp.flush()
            path = Path(tmp.name)
        try:
            redact_file(path)
            text = path.read_text()
            self.assertIn("password=[REDACTED]", text)
            self.assertIn("api_key=[REDACTED]", text)
            self.assertNotIn("supersecret", text)
            self.assertNotIn("abc123", text)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
