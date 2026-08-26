"""Vultr API v1 constants from official reference (2020-09-11)."""

from __future__ import annotations

API_BASE = "https://api.vultr.com"
API_VERSION = "v1"

# Manual: create server from snapshot → OSID 164 + SNAPSHOTID
OSID_SNAPSHOT = 164

# Manual HTTP response codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_PRECONDITION_FAILED = 412
HTTP_SERVER_ERROR = 500
HTTP_RATE_LIMIT = 503

VULTR_HTTP_MESSAGES = {
    HTTP_BAD_REQUEST: "Invalid API location. Check the URL.",
    HTTP_FORBIDDEN: "Invalid or missing API key.",
    HTTP_METHOD_NOT_ALLOWED: "Invalid HTTP method.",
    HTTP_PRECONDITION_FAILED: "Request failed. Check response body.",
    HTTP_SERVER_ERROR: "Internal server error. Try again later.",
    HTTP_RATE_LIMIT: "Rate limit hit (~2 req/s average). Retry later.",
}
