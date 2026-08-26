#!/usr/bin/env python3
"""Encrypt log files with Fernet (AES-128-CBC + HMAC-SHA256). Key from Bitwarden."""

from __future__ import annotations

import sys
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def _fernet_from_key(key_material: str) -> Fernet:
    """Accept a url-safe base64 Fernet key or derive-compatible raw secret."""
    key = key_material.strip().encode("utf-8")
    try:
        return Fernet(key)
    except Exception:
        import base64
        import hashlib

        derived = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(derived)


def encrypt_file(filepath: Path, key_material: str) -> Path:
    fernet = _fernet_from_key(key_material)
    plaintext = filepath.read_bytes()
    encrypted = fernet.encrypt(plaintext)
    out_path = filepath.with_suffix(filepath.suffix + ".enc")
    out_path.write_bytes(encrypted)
    filepath.unlink(missing_ok=True)
    return out_path


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: encrypt_logs.py <logfile> <encryption_key>", file=sys.stderr)
        raise SystemExit(1)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Log file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        out = encrypt_file(path, sys.argv[2])
    except InvalidToken as exc:
        print(f"Encryption failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(str(out))


if __name__ == "__main__":
    main()
