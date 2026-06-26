"""Public Studio CLI whitelist tests."""

import os

os.environ.setdefault("STUDIO_MODE", "public")

from web_gateway.studio_security import validate_public_cli


def test_public_new_site_allowed():
    assert validate_public_cli("new", ["site", "--name", "demo"]) is None


def test_public_deploy_railway_blocked():
    err = validate_public_cli("deploy", ["railway", "--name", "x"])
    assert err is not None


def test_public_repo_token_blocked():
    err = validate_public_cli("deploy", ["github", "--repo", "https://token@github.com/x/y.git"])
    assert err is not None


def test_public_ai_allowed():
    assert validate_public_cli("ai", ["suggest-template", "--industry", "dental"]) is None
