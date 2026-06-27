"""Agent registry tests."""

from agents.registry import agents_for_job_type, list_agents


def test_eight_agents_in_registry():
    agents = list_agents()
    assert len(agents) == 8


def test_claw_handles_file_jobs():
    assert "claw-core" in agents_for_job_type("file_write")
    assert "claw-core" in agents_for_job_type("build_site")
