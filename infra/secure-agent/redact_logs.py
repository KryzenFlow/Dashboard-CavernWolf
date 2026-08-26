#!/usr/bin/env python3
"""Redact sensitive patterns from log files before encryption."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(password\s*=\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(api[_-]?key\s*=\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(token\s*=\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(authorization\s*:\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"\b\d{6,}\b"), "[REDACTED_ID]"),
]


def redact_file(filepath: Path) -> None:
    content = filepath.read_text(encoding="utf-8", errors="replace")
    for pattern, replacement in _PATTERNS:
        content = pattern.sub(replacement, content)
    filepath.write_text(content, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: redact_logs.py <logfile>", file=sys.stderr)
        raise SystemExit(1)
    redact_file(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
